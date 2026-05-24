import json
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from system.forms import (
    PortalAuthenticationForm,
    PortalPasswordResetRequestForm,
    PortalRegistrationForm,
    PortalSetPasswordForm,
)
from system.constants import CheckoutAction
from system.models import Person
from system.models import PreRegistration, PreRegistrationStatus
from system.models import SubscriptionPlan
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.services import asaas_client
from system.services.coupon import CouponError, apply_coupon, mark_coupon_used, validate_coupon
from system.services.class_catalog import get_ibjjf_age_category_payload
from system.services.class_overview import get_registration_catalog_payload
from system.services.registration_checkout import (
    get_plan_catalog_payload,
    get_product_catalog_payload,
    create_product_only_order,
    gross_up_order_for_checkout,
    parse_selected_products,
    resolve_selected_product_items,
    build_order_item_product_name,
)
from system.services.registration_validation import validate_registration_step
from system.utils import ensure_formatted_cpf
from system.services import (
    authenticate_portal_identity,
    create_password_reset_token,
    get_valid_password_reset_token,
    login_portal_identity,
    logout_portal_identity,
    reset_portal_password,
)


class PortalRegisterView(FormView):
    form_class = PortalRegistrationForm
    template_name = "login/register.html"
    success_url = reverse_lazy("system:login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
            pre_registration_id = self.request.session.get("pending_pre_registration_id")
            if pre_registration_id:
                pr = PreRegistration.objects.filter(pk=pre_registration_id).first()
                if pr and pr.form_snapshot:
                    kwargs["initial"] = pr.form_snapshot
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["registration_initial_step"] = self._get_initial_step(form)
        context["selected_other_type_code"] = form["other_type_code"].value() or ""
        context["registration_catalog_json"] = json.dumps(
            get_registration_catalog_payload(), ensure_ascii=False
        )
        context["ibjjf_categories_json"] = json.dumps(
            get_ibjjf_age_category_payload(), ensure_ascii=False
        )
        context["plan_catalog_json"] = json.dumps(
            get_plan_catalog_payload(), ensure_ascii=False
        )
        context["product_catalog_json"] = json.dumps(
            get_product_catalog_payload(), ensure_ascii=False
        )
        context["post_plan_payment_complete"] = self.request.session.get("post_plan_payment_complete", False)
        context["plan_is_trial"] = self.request.session.get("plan_is_trial", False)
        context["post_materials_payment_complete"] = self.request.session.get("post_materials_payment_complete", False)
        context["post_materials_skipped"] = self.request.session.get("post_materials_skipped", False)
        context["plan_order_json"] = json.dumps(
            self._get_registration_order_or_pre_registration_summary("plan"), ensure_ascii=False
        )
        context["materials_order_json"] = json.dumps(
            self._get_registration_order_or_pre_registration_summary("materials"), ensure_ascii=False
        )
        context["pending_person_json"] = json.dumps(
            self._get_pending_person_summary(), ensure_ascii=False
        )
        context["fee_config_json"] = json.dumps({
            "pixFixedFee": float(settings.ASAAS_PIX_FIXED_FEE),
            "creditCardPercentFee": float(settings.ASAAS_CREDIT_PERCENT_FEE),
            "creditCardFixedFee": float(settings.ASAAS_CREDIT_FIXED_FEE),
            "creditCardFeePassThrough": bool(settings.CREDIT_CARD_FEE_PASS_THROUGH),
            "pixFeePassThrough": bool(settings.PIX_FEE_PASS_THROUGH),
        }, ensure_ascii=False)
        return context

    def form_valid(self, form):
        pre_registration = self._save_pre_registration(form)
        self.request.session["pending_pre_registration_id"] = pre_registration.pk
        self.request.session.pop("pending_registration_person_id", None)
        self.request.session.pop("post_plan_payment_complete", None)
        self.request.session.pop("post_materials_payment_complete", None)
        self.request.session.pop("post_materials_skipped", None)

        checkout_action = form.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER
        if checkout_action == CheckoutAction.PAY_LATER:
            # Marca aula experimental no snapshot e avança o wizard
            snapshot = pre_registration.form_snapshot or {}
            snapshot["trial_requested"] = True
            pre_registration.form_snapshot = snapshot
            pre_registration.save(update_fields=["form_snapshot", "updated_at"])
            self.request.session["post_plan_payment_complete"] = True
            self.request.session["plan_is_trial"] = True
            self.request.session.pop("plan_order_id", None)
            return redirect("system:register")

        try:
            invoice_url = self._create_pre_registration_plan_payment(
                pre_registration,
                checkout_action,
            )
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return redirect("system:register")
        except asaas_client.AsaasClientError:
            messages.error(
                self.request,
                "Pagamento Asaas indisponível no momento. Tente novamente em instantes.",
            )
            return redirect("system:register")
        pre_registration.mark_awaiting_payment()
        return redirect(invoice_url)

    def _save_pre_registration(self, form):
        snapshot = self._build_form_snapshot()
        if not self.request.session.session_key:
            self.request.session.create()
        pre_registration_id = self.request.session.get("pending_pre_registration_id")
        defaults = {
            "session_key": self.request.session.session_key or "",
            "registration_profile": form.cleaned_data.get("registration_profile", ""),
            "holder_cpf": self._resolve_primary_cpf(form.cleaned_data),
            "holder_email": self._resolve_primary_email(form.cleaned_data),
            "form_snapshot": snapshot,
            "selected_plan_id": form.cleaned_data.get("selected_plan"),
            "checkout_action": form.cleaned_data.get("checkout_action") or CheckoutAction.PAY_LATER,
            "status": PreRegistrationStatus.DRAFT,
        }
        if pre_registration_id:
            updated = PreRegistration.objects.filter(pk=pre_registration_id).first()
            if updated is not None and updated.status != PreRegistrationStatus.FINALIZED:
                for key, value in defaults.items():
                    setattr(updated, key, value)
                updated.save()
                return updated
        return PreRegistration.objects.create(**defaults)

    # Campos que o Django processa como lista (MultipleChoiceField) — sempre salvar como list no snapshot
    _MULTI_VALUE_FORM_FIELDS = {
        "holder_class_groups",
        "dependent_class_groups",
        "student_class_groups",
    }

    def _build_form_snapshot(self):
        snapshot = {}
        for key, values in self.request.POST.lists():
            if key == "csrfmiddlewaretoken":
                continue
            if key in self._MULTI_VALUE_FORM_FIELDS:
                snapshot[key] = values  # sempre lista para MultipleChoiceField
            else:
                snapshot[key] = values if len(values) > 1 else values[0]
        return snapshot

    @staticmethod
    def _snapshot_scalar(snapshot, key, default=""):
        """Lê um campo scalar do snapshot, normalizando caso tenha sido salvo como lista."""
        value = snapshot.get(key, default)
        if isinstance(value, list):
            value = value[0] if value else default
        return value or default

    def _resolve_primary_cpf(self, cleaned_data):
        return (
            cleaned_data.get("holder_cpf")
            or cleaned_data.get("guardian_cpf")
            or cleaned_data.get("other_cpf")
            or ""
        )

    def _resolve_primary_email(self, cleaned_data):
        return (
            cleaned_data.get("holder_email")
            or cleaned_data.get("guardian_email")
            or cleaned_data.get("other_email")
            or ""
        )

    def _create_pre_registration_plan_payment(self, pre_registration, checkout_action):
        from system.services.stripe_checkout import (
            StripeCheckoutError,
            create_subscription_session_for_pre_registration,
        )

        snapshot = pre_registration.form_snapshot or {}
        selected_plans = self._parse_selected_plan_payload(snapshot)
        if not selected_plans:
            raise ValueError("Selecione ao menos um plano para pagar.")

        plans = list(SubscriptionPlan.objects.filter(
            pk__in=[item["plan_id"] for item in selected_plans],
            is_active=True,
        ))
        plans_by_id = {plan.pk: plan for plan in plans}
        missing = [item["plan_id"] for item in selected_plans if item["plan_id"] not in plans_by_id]
        if missing:
            raise ValueError("Selecione apenas planos válidos.")

        total = sum((plans_by_id[item["plan_id"]].price for item in selected_plans), Decimal("0.00"))
        if total <= 0:
            raise ValueError("Plano sem valor cobrável.")

        # Aplicar cupom de desconto — válido para todos os gateways
        coupon_code = self._snapshot_scalar(snapshot, "coupon_code")
        coupon = None
        discount_amount = Decimal("0.00")
        if coupon_code:
            try:
                coupon = validate_coupon(coupon_code)
                total, discount_amount = apply_coupon(coupon, total)
            except CouponError as exc:
                raise ValueError(str(exc))

        if checkout_action == CheckoutAction.STRIPE_CARD:
            coupon_info = (
                {"coupon_code": coupon.code, "discount_amount": str(discount_amount)}
                if coupon else None
            )
            try:
                session = create_subscription_session_for_pre_registration(
                    pre_registration, plans_by_id, selected_plans,
                    final_total=total, coupon_info=coupon_info,
                )
            except StripeCheckoutError as exc:
                raise ValueError(str(exc))
            if coupon:
                mark_coupon_used(coupon)
            return session["url"]

        customer_id = self._ensure_pre_registration_asaas_customer(pre_registration)
        success_url = (
            settings.SITE_BASE_URL.rstrip("/")
            + reverse("system:payment-success")
            + f"?pre_registration_id={pre_registration.pk}&stage=plan"
        )
        description = "Mensalidade LV Jiu Jitsu — pré-cadastro #{0}".format(pre_registration.pk)
        due_date = timezone.localdate() + timedelta(days=settings.ASAAS_CARD_DUE_DAYS)

        if checkout_action == CheckoutAction.PIX:
            payment = asaas_client.create_pix_payment(
                customer_id=customer_id,
                value=total,
                due_date=due_date,
                description=description,
                external_reference=f"pre-registration:{pre_registration.pk}:plan",
                success_url=success_url,
            )
        else:
            payment = asaas_client.create_credit_card_payment(
                customer_id=customer_id,
                value=total,
                due_date=due_date,
                description=description,
                external_reference=f"pre-registration:{pre_registration.pk}:plan",
                installment_count=1,
                success_url=success_url,
            )

        invoice_url = payment.get("invoiceUrl") or ""
        payment_id = payment.get("id") or ""
        if not invoice_url or not payment_id:
            raise asaas_client.AsaasClientError("Resposta Asaas sem invoiceUrl ou id.")

        coupon_info = {}
        if coupon:
            coupon_info = {
                "coupon_code": coupon.code,
                "discount_amount": str(discount_amount),
            }
            mark_coupon_used(coupon)

        snapshot["plan_payment"] = {
            "asaas_payment_id": payment_id,
            "total": str(total),
            "items": [
                {
                    "label": item.get("label", ""),
                    "plan_id": item["plan_id"],
                    "plan_name": plans_by_id[item["plan_id"]].display_name,
                    "price": str(plans_by_id[item["plan_id"]].price),
                }
                for item in selected_plans
            ],
            **coupon_info,
        }
        pre_registration.form_snapshot = snapshot
        pre_registration.save(update_fields=["form_snapshot", "updated_at"])
        return invoice_url

    def _parse_selected_plan_payload(self, snapshot):
        raw = snapshot.get("selected_plans_payload") or ""
        result = []
        if raw:
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                payload = []
            if isinstance(payload, list):
                for item in payload:
                    try:
                        plan_id = int(item.get("plan_id") or 0)
                    except (TypeError, ValueError, AttributeError):
                        continue
                    if plan_id:
                        result.append({"plan_id": plan_id, "label": item.get("label", "")})
        if result:
            return result
        try:
            plan_id = int(snapshot.get("selected_plan") or 0)
        except (TypeError, ValueError):
            plan_id = 0
        return [{"plan_id": plan_id, "label": ""}] if plan_id else []

    def _ensure_pre_registration_asaas_customer(self, pre_registration):
        snapshot = pre_registration.form_snapshot or {}
        payment_meta = snapshot.get("asaas_customer") or {}
        if payment_meta.get("id"):
            return payment_meta["id"]
        profile = snapshot.get("registration_profile") or pre_registration.registration_profile
        prefix = "guardian" if profile == "guardian" else "holder"
        customer = asaas_client.create_customer(
            name=snapshot.get(f"{prefix}_name") or pre_registration.holder_cpf,
            cpf_cnpj=snapshot.get(f"{prefix}_cpf") or pre_registration.holder_cpf,
            email=snapshot.get(f"{prefix}_email") or None,
            phone=snapshot.get(f"{prefix}_phone") or None,
            external_reference=f"pre-registration:{pre_registration.pk}",
            postal_code=snapshot.get(f"{prefix}_postal_code") or None,
            address=snapshot.get(f"{prefix}_address") or None,
            address_number=snapshot.get(f"{prefix}_address_number") or None,
            address_complement=snapshot.get(f"{prefix}_address_complement") or None,
            address_neighborhood=snapshot.get(f"{prefix}_address_neighborhood") or None,
            city=snapshot.get(f"{prefix}_city") or None,
        )
        customer_id = customer.get("id") if isinstance(customer, dict) else ""
        if not customer_id:
            raise asaas_client.AsaasClientError("Resposta Asaas sem id de cliente.")
        snapshot["asaas_customer"] = {"id": customer_id}
        pre_registration.form_snapshot = snapshot
        pre_registration.save(update_fields=["form_snapshot", "updated_at"])
        return customer_id

    def _get_pending_person_summary(self):
        pre_registration_id = self.request.session.get("pending_pre_registration_id")
        if pre_registration_id:
            pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
            if pre_registration is not None:
                return self._build_pending_summary_from_pre_registration(pre_registration)

        person_id = self.request.session.get("pending_registration_person_id")
        if not person_id:
            return None
        try:
            person = Person.objects.select_related(
                "class_group__class_category", "person_type"
            ).get(pk=person_id)
        except Person.DoesNotExist:
            return None

        class_group_name = str(person.class_group) if person.class_group else ""
        base = {
            "id": person.pk,
            "full_name": person.full_name,
            "email": person.email or "",
            "phone": person.phone or "",
            "class_group_name": class_group_name,
            "person_type_code": person.person_type.code if person.person_type else "",
        }

        from system.models import PersonRelationship, PersonRelationshipKind
        students = list(
            PersonRelationship.objects.filter(
                source_person=person,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).select_related("target_person__class_group__class_category")
        )
        if students:
            base["students"] = [
                {
                    "full_name": rel.target_person.full_name,
                    "class_group_name": str(rel.target_person.class_group) if rel.target_person.class_group else "",
                }
                for rel in students
            ]
        return base

    def _build_pending_summary_from_pre_registration(self, pre_registration):
        data = pre_registration.form_snapshot or {}
        profile = data.get("registration_profile") or pre_registration.registration_profile
        is_guardian = profile == "guardian"
        base_prefix = "guardian" if is_guardian else "holder"
        base = {
            "id": None,
            "full_name": data.get(f"{base_prefix}_name", ""),
            "email": data.get(f"{base_prefix}_email", ""),
            "phone": data.get(f"{base_prefix}_phone", ""),
            "class_group_name": "",
            "person_type_code": "guardian" if is_guardian else "student",
        }
        students = []
        if is_guardian and data.get("student_name"):
            students.append({"full_name": data.get("student_name", ""), "class_group_name": ""})
        if (not is_guardian) and data.get("dependent_name"):
            students.append({"full_name": data.get("dependent_name", ""), "class_group_name": ""})
        if students:
            base["students"] = students
        return base

    def _get_order_summary(self, order_id):
        if not order_id:
            return None
        try:
            order = RegistrationOrder.objects.prefetch_related("items").select_related("plan").get(pk=order_id)
        except RegistrationOrder.DoesNotExist:
            return None
        items = [
            {
                "name": item.product_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
            }
            for item in order.items.all()
        ]
        return {
            "id": order.pk,
            "plan_name": order.plan.display_name if order.plan else None,
            "plan_price": str(order.plan_price) if order.plan_price else None,
            "total": str(order.total),
            "items": items,
        }

    def _get_registration_order_or_pre_registration_summary(self, kind):
        order_key = "plan_order_id" if kind == "plan" else "materials_order_id"
        order_summary = self._get_order_summary(self.request.session.get(order_key))
        if order_summary:
            return order_summary
        pre_registration_id = self.request.session.get("pending_pre_registration_id")
        if not pre_registration_id:
            return None
        pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if pre_registration is None:
            return None
        snapshot = pre_registration.form_snapshot or {}
        if kind == "plan":
            plan_payment = snapshot.get("plan_payment") or {}
            items = plan_payment.get("items") or []
            return {
                "id": None,
                "plan_name": " + ".join(item.get("plan_name", "") for item in items if item.get("plan_name")),
                "plan_price": plan_payment.get("total"),
                "total": plan_payment.get("total"),
                "items": items,
            }
        materials_payment = snapshot.get("materials_payment") or {}
        return {
            "id": None,
            "plan_name": None,
            "plan_price": None,
            "total": materials_payment.get("total"),
            "items": materials_payment.get("items") or [],
        }

    def _get_initial_step(self, form):
        if not form.is_bound or not form.errors:
            return 1

        medical_fields = {
            "holder_blood_type",
            "holder_allergies",
            "holder_injuries",
            "holder_emergency_contact",
            "holder_has_martial_art",
            "holder_martial_art",
            "holder_martial_art_graduation",
            "holder_jiu_jitsu_belt",
            "holder_jiu_jitsu_stripes",
            "dependent_blood_type",
            "dependent_allergies",
            "dependent_injuries",
            "dependent_emergency_contact",
            "dependent_has_martial_art",
            "dependent_martial_art",
            "dependent_martial_art_graduation",
            "dependent_jiu_jitsu_belt",
            "dependent_jiu_jitsu_stripes",
            "student_blood_type",
            "student_allergies",
            "student_injuries",
            "student_emergency_contact",
            "student_has_martial_art",
            "student_martial_art",
            "student_martial_art_graduation",
            "student_jiu_jitsu_belt",
            "student_jiu_jitsu_stripes",
        }
        class_fields = {
            "holder_class_groups",
            "dependent_class_groups",
            "student_class_groups",
            "extra_dependents_payload",
        }
        registration_fields = {
            "registration_profile",
            "include_dependent",
            "other_type_code",
        }

        error_fields = set(form.errors.keys())
        if error_fields & medical_fields:
            return 4
        if error_fields & class_fields:
            return 3
        if error_fields - registration_fields:
            return 2
        return 1


class RegistrationStepValidationView(View):
    def post(self, request, *args, **kwargs):
        errors = validate_registration_step(request.POST)
        return JsonResponse({"valid": not errors, "errors": errors})


class ValidateCouponView(View):
    def post(self, request, *args, **kwargs):
        from decimal import Decimal

        code = request.POST.get("coupon_code") or ""
        raw_total = request.POST.get("total") or "0"

        try:
            total = Decimal(raw_total)
        except Exception:
            return JsonResponse({"valid": False, "message": "Total inválido."}, status=400)

        try:
            coupon = validate_coupon(code)
        except CouponError as exc:
            return JsonResponse({"valid": False, "message": str(exc)})

        discounted_total, discount_amount = apply_coupon(coupon, total)
        from system.models.coupon import DiscountType
        label = (
            f"{coupon.discount_value}%"
            if coupon.discount_type == DiscountType.PERCENT
            else f"R$ {coupon.discount_value:.2f}".replace(".", ",")
        )
        return JsonResponse({
            "valid": True,
            "message": f"Cupom aplicado: {label} de desconto.",
            "discount_amount": str(discount_amount),
            "discounted_total": str(discounted_total),
            "coupon_code": coupon.code,
        })


class RegistrationCpfAvailabilityView(View):
    def get(self, request, *args, **kwargs):
        raw_cpf = request.GET.get("cpf", "")
        if not raw_cpf:
            return JsonResponse({"valid": False, "available": False, "error": "Informe o CPF."})
        try:
            cpf = ensure_formatted_cpf(raw_cpf)
        except ValueError as exc:
            return JsonResponse({"valid": False, "available": False, "error": str(exc)})
        exists = Person.objects.filter(cpf=cpf, is_active=True).exists()
        if exists:
            return JsonResponse({
                "valid": True,
                "available": False,
                "error": "CPF já cadastrado no sistema.",
            })
        return JsonResponse({"valid": True, "available": True, "error": ""})


class PortalLoginView(FormView):
    form_class = PortalAuthenticationForm
    template_name = "login/login_form.html"

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "portal_account", None) is not None or getattr(
            request, "portal_is_technical_admin", False
        ):
            return redirect("system:dashboard-redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        identity = authenticate_portal_identity(
            identifier=form.cleaned_data["identifier"],
            password=form.cleaned_data["password"],
        )

        if identity is None:
            form.add_error(None, "CPF, acesso técnico ou senha inválidos.")
            return self.form_invalid(form)

        if identity.get("blocked_reason") == "payment_pending":
            pending_order = identity.get("pending_order")
            if pending_order is not None:
                self.request.session["pending_checkout_order_id"] = pending_order.pk
                messages.info(
                    self.request,
                    "Seu cadastro está aguardando a confirmação do pagamento. "
                    "Vamos redirecioná-lo para concluir agora.",
                )
                return redirect(
                    "system:payment-checkout", order_id=pending_order.pk
                )
            form.add_error(
                None,
                "Seu cadastro está aguardando a confirmação do pagamento. "
                "Conclua o pagamento para acessar o sistema.",
            )
            return self.form_invalid(form)

        login_portal_identity(
            self.request,
            portal_account=identity["portal_account"],
            technical_admin_user=identity["technical_admin_user"],
        )
        redirect_to = self.request.POST.get("next") or self.request.GET.get("next")
        return redirect(redirect_to or reverse("system:dashboard-redirect"))


class PortalLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout_portal_identity(request)
        return redirect("system:root")

    def post(self, request, *args, **kwargs):
        logout_portal_identity(request)
        return redirect("system:root")


class PortalPasswordResetView(FormView):
    form_class = PortalPasswordResetRequestForm
    template_name = "login/password_reset_form.html"
    success_url = reverse_lazy("system:password-reset-done")

    def form_valid(self, form):
        create_password_reset_token(form.cleaned_data["cpf"], self.request)
        return super().form_valid(form)


class PortalPasswordResetDoneView(TemplateView):
    template_name = "login/password_reset_done.html"


class PortalPasswordResetConfirmView(FormView):
    form_class = PortalSetPasswordForm
    template_name = "login/password_reset_confirm.html"
    success_url = reverse_lazy("system:password-reset-complete")

    def dispatch(self, request, *args, **kwargs):
        self.reset_token = get_valid_password_reset_token(kwargs["token"])
        if self.reset_token is None:
            raise Http404("Token de redefinição inválido.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        reset_portal_password(self.reset_token, form.cleaned_data["new_password1"])
        return super().form_valid(form)


class PortalPasswordResetCompleteView(TemplateView):
    template_name = "login/password_reset_complete.html"


class ChromeDevtoolsProbeView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=204, content_type="application/json")




class MaterialsCheckoutView(View):
    def post(self, request, *args, **kwargs):
        pre_registration_id = request.session.get("pending_pre_registration_id")
        if pre_registration_id:
            return self._post_for_pre_registration(request, pre_registration_id)

        person_id = request.session.get("pending_registration_person_id")
        if not person_id:
            return redirect("system:register")

        try:
            person = Person.objects.get(pk=person_id)
        except Person.DoesNotExist:
            return redirect("system:register")

        raw_payload = request.POST.get("selected_products_payload", "")
        selected = parse_selected_products(raw_payload)
        if not selected:
            request.session["post_materials_payment_complete"] = True
            return redirect("system:register")

        try:
            items = resolve_selected_product_items(selected)
        except ValueError:
            messages.error(request, "Selecione apenas materiais válidos com estoque disponível.")
            return redirect("system:register")

        order = create_product_only_order(person, items)
        if order is None:
            request.session["post_materials_payment_complete"] = True
            return redirect("system:register")

        request.session["pending_checkout_order_id"] = order.pk
        checkout_action = request.POST.get("checkout_action") or CheckoutAction.PAY_LATER
        gross_up_order_for_checkout(order, checkout_action)
        if checkout_action == CheckoutAction.ASAAS_CARD:
            return redirect("system:asaas-card-create", order_id=order.pk)
        if checkout_action == CheckoutAction.PIX:
            return redirect("system:asaas-pix-create", order_id=order.pk)

        request.session["post_materials_payment_complete"] = True
        request.session["materials_order_id"] = order.pk
        return redirect("system:register")

    def _post_for_pre_registration(self, request, pre_registration_id):
        pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if pre_registration is None:
            return redirect("system:register")

        raw_payload = request.POST.get("selected_products_payload", "")
        selected = parse_selected_products(raw_payload)
        snapshot = pre_registration.form_snapshot or {}
        snapshot["selected_products_payload"] = raw_payload or "[]"
        snapshot["materials_checkout_action"] = request.POST.get("checkout_action") or CheckoutAction.PAY_LATER
        pre_registration.form_snapshot = snapshot
        pre_registration.save(update_fields=["form_snapshot", "updated_at"])

        if not selected:
            request.session["post_materials_skipped"] = True
            request.session.pop("post_materials_payment_complete", None)
            return redirect("system:register")

        try:
            items = resolve_selected_product_items(selected)
        except ValueError:
            messages.error(request, "Selecione apenas materiais válidos com estoque disponível.")
            return redirect("system:register")

        checkout_action = request.POST.get("checkout_action") or CheckoutAction.PAY_LATER
        if checkout_action == CheckoutAction.PAY_LATER:
            request.session["post_materials_skipped"] = True
            request.session.pop("post_materials_payment_complete", None)
            return redirect("system:register")

        try:
            invoice_url = self._create_pre_registration_materials_payment(
                pre_registration,
                items,
                checkout_action,
            )
        except asaas_client.AsaasClientError:
            messages.error(
                request,
                "Pagamento Asaas dos materiais indisponível no momento. Tente novamente em instantes.",
            )
            return redirect("system:register")
        return redirect(invoice_url)

    def _create_pre_registration_materials_payment(self, pre_registration, items, checkout_action):
        total = sum(
            (selection["product"].unit_price * selection["quantity"] for selection in items),
            Decimal("0.00"),
        )
        if total <= 0:
            raise asaas_client.AsaasClientError("Pedido de materiais sem valor cobrável.")

        customer_id = PortalRegisterView()._ensure_pre_registration_asaas_customer(pre_registration)
        success_url = (
            settings.SITE_BASE_URL.rstrip("/")
            + reverse("system:payment-success")
            + f"?pre_registration_id={pre_registration.pk}&stage=materials"
        )
        due_date = timezone.localdate() + timedelta(days=settings.ASAAS_CARD_DUE_DAYS)
        description = "Materiais LV Jiu Jitsu — pré-cadastro #{0}".format(pre_registration.pk)

        if checkout_action == CheckoutAction.PIX:
            payment = asaas_client.create_pix_payment(
                customer_id=customer_id,
                value=total,
                due_date=due_date,
                description=description,
                external_reference=f"pre-registration:{pre_registration.pk}:materials",
                success_url=success_url,
            )
        else:
            payment = asaas_client.create_credit_card_payment(
                customer_id=customer_id,
                value=total,
                due_date=due_date,
                description=description,
                external_reference=f"pre-registration:{pre_registration.pk}:materials",
                installment_count=1,
                success_url=success_url,
            )
        invoice_url = payment.get("invoiceUrl") or ""
        payment_id = payment.get("id") or ""
        if not invoice_url or not payment_id:
            raise asaas_client.AsaasClientError("Resposta Asaas sem invoiceUrl ou id.")

        snapshot = pre_registration.form_snapshot or {}
        snapshot["materials_payment"] = {
            "asaas_payment_id": payment_id,
            "total": str(total),
            "items": [
                {
                    "name": build_order_item_product_name(selection["product"], selection["variant"]),
                    "quantity": selection["quantity"],
                    "unit_price": str(selection["product"].unit_price),
                    "subtotal": str(selection["product"].unit_price * selection["quantity"]),
                }
                for selection in items
            ],
        }
        pre_registration.form_snapshot = snapshot
        pre_registration.save(update_fields=["form_snapshot", "updated_at"])
        return invoice_url


class ResetRegistrationView(View):
    """Limpa estado de cadastro da sessão e redireciona para /register/ limpo."""

    _SESSION_KEYS = (
        "pending_pre_registration_id",
        "pending_registration_person_id",
        "post_plan_payment_complete",
        "post_materials_payment_complete",
        "post_materials_skipped",
        "plan_order_id",
        "materials_order_id",
        "plan_is_trial",
    )

    def get(self, request, *args, **kwargs):
        for key in self._SESSION_KEYS:
            request.session.pop(key, None)
        return redirect("system:register")


class FinalizeRegistrationView(View):
    """Ativa person.is_active=True, faz login e redireciona para dashboard."""

    def post(self, request, *args, **kwargs):
        pre_registration_id = request.session.get("pending_pre_registration_id")
        if pre_registration_id:
            return self._finalize_pre_registration(request, pre_registration_id)

        person_id = request.session.get("pending_registration_person_id")
        if not person_id:
            return redirect("system:register")

        try:
            person = Person.objects.select_related("access_account").get(pk=person_id)
        except Person.DoesNotExist:
            return redirect("system:register")

        if not person.is_active:
            person.is_active = True
            person.save(update_fields=["is_active", "updated_at"])

        portal_account = getattr(person, "access_account", None)
        if portal_account and not portal_account.is_active:
            portal_account.is_active = True
            portal_account.save(update_fields=["is_active", "updated_at"])

        for key in (
            "pending_registration_person_id",
            "post_plan_payment_complete",
            "post_materials_payment_complete",
            "plan_order_id",
            "materials_order_id",
        ):
            request.session.pop(key, None)

        if portal_account:
            login_portal_identity(request, portal_account=portal_account)

        messages.success(request, "Cadastro finalizado com sucesso! Seja bem-vindo.")
        return redirect("system:dashboard-redirect")

    def _finalize_pre_registration(self, request, pre_registration_id):
        pre_registration = PreRegistration.objects.filter(pk=pre_registration_id).first()
        if pre_registration is None:
            return redirect("system:register")
        if pre_registration.status == PreRegistrationStatus.FINALIZED and pre_registration.finalized_person:
            return redirect("system:dashboard-redirect")

        form_data = self._normalize_snapshot_for_form(pre_registration.form_snapshot or {})
        form = PortalRegistrationForm(data=form_data)
        if not form.is_valid():
            messages.error(request, "Revise os dados do cadastro antes de finalizar.")
            return redirect("system:register")

        created_people = form.save()
        primary_person = (
            created_people.get("holder")
            or created_people.get("guardian")
            or created_people.get("other")
        )
        if primary_person is None:
            messages.error(request, "Não foi possível finalizar o cadastro.")
            return redirect("system:register")

        if not primary_person.is_active:
            primary_person.is_active = True
            primary_person.save(update_fields=["is_active", "updated_at"])
        portal_account = getattr(primary_person, "access_account", None)
        if portal_account and not portal_account.is_active:
            portal_account.is_active = True
            portal_account.save(update_fields=["is_active", "updated_at"])

        pre_registration.mark_finalized(primary_person)

        # Sincroniza o pagamento já realizado no Asaas/Stripe com a RegistrationOrder criada pela finalização.
        # form.save() → create_portal_registration() → create_registration_order() cria uma ordem PENDING para
        # a pessoa recém-criada. Quando o pré-cadastro já teve pagamento confirmado (plan_paid=True no snapshot),
        # essa ordem deve ser marcada como PAID para não bloquear o login do usuário.
        snapshot = pre_registration.form_snapshot or {}
        order = created_people.get("order")
        if order is not None and snapshot.get("plan_paid") and order.payment_status == PaymentStatus.PENDING:
            plan_payment = snapshot.get("plan_payment") or {}
            asaas_payment_id = plan_payment.get("asaas_payment_id") or ""
            order.payment_status = PaymentStatus.PAID
            order.paid_at = timezone.now()
            if asaas_payment_id:
                order.asaas_payment_id = asaas_payment_id
            order.save(update_fields=["payment_status", "paid_at", "asaas_payment_id", "updated_at"])
            from system.services.membership import activate_membership_from_paid_order
            activate_membership_from_paid_order(
                order,
                notes="Pagamento confirmado via pré-cadastro.",
            )

        # Aula experimental: criar RegistrationOrder pendente e TrialAccessGrant
        if snapshot.get("trial_requested"):
            self._grant_trial_for_pre_registration(pre_registration, primary_person)

        for key in (
            "pending_pre_registration_id",
            "pending_registration_person_id",
            "post_plan_payment_complete",
            "post_materials_payment_complete",
            "post_materials_skipped",
            "plan_order_id",
            "materials_order_id",
            "plan_is_trial",
        ):
            request.session.pop(key, None)

        if portal_account:
            login_portal_identity(request, portal_account=portal_account)
        messages.success(request, "Cadastro finalizado com sucesso! Seja bem-vindo.")
        return redirect("system:dashboard-redirect")

    @staticmethod
    def _normalize_snapshot_for_form(snapshot):
        """Prepara o snapshot do banco para uso como `data` no PortalRegistrationForm.

        Corrige dois problemas acumulados em snapshots antigos:
        - MultipleChoiceField (class_groups) salvo como string quando havia apenas 1 valor → converte para lista.
        - Campos scalar salvos como lista por duplicata de input no template → toma o primeiro valor.
        - Entradas de dicionário aninhado (plan_payment, etc.) não são campos do form → removidas.
        """
        MULTI_VALUE = {"holder_class_groups", "dependent_class_groups", "student_class_groups"}
        SKIP_DICT_VALUES = True  # dicts aninhados não são campos do form

        result = {}
        for key, value in snapshot.items():
            if SKIP_DICT_VALUES and isinstance(value, dict):
                continue  # plan_payment, materials_payment — não são campos do form
            if key in MULTI_VALUE:
                # Garante que MultipleChoiceField sempre receba lista
                if isinstance(value, list):
                    result[key] = value
                elif value:
                    result[key] = [value]
                else:
                    result[key] = []
            elif isinstance(value, list):
                # Campo scalar armazenado como lista por bug de duplicata — usa primeiro valor
                result[key] = value[0] if value else ""
            else:
                result[key] = value
        return result

    def _grant_trial_for_pre_registration(self, pre_registration, primary_person):
        from decimal import Decimal
        from system.models.registration_order import (
            OrderKind, PaymentProvider, PaymentStatus, RegistrationOrder,
        )
        from system.models.plan import SubscriptionPlan
        from system.services.trial_access import grant_trial_for_order

        plan = None
        if pre_registration.selected_plan_id:
            plan = SubscriptionPlan.objects.filter(pk=pre_registration.selected_plan_id).first()

        trial_order = RegistrationOrder.objects.create(
            person=primary_person,
            plan=plan,
            kind=OrderKind.SUBSCRIPTION,
            payment_status=PaymentStatus.PENDING,
            payment_provider=PaymentProvider.NONE,
            total=plan.price if plan else Decimal("0"),
            plan_price=plan.price if plan else Decimal("0"),
            notes="Aula experimental via pré-cadastro.",
        )
        grant_trial_for_order(trial_order, notes="Aula experimental concedida no pré-cadastro.")
