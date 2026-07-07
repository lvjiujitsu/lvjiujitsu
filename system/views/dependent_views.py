import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.formats import date_format
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views import View
from django.views.generic import TemplateView

from system.constants import DependentFinancialMode
from system.forms import DependentProfileForm, DependentRegistrationForm
from system.models import AuditAction, AuditModule
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.services.audit import record_audit_event
from system.services.dependent_registration import (
    create_dependent_pre_registration,
    finalize_dependent_registration,
    get_pending_dependent_pre_registration,
    initial_from_pre_registration,
    save_checkout_url,
    update_dependent_pre_registration,
)
from system.services.class_catalog import get_ibjjf_age_category_payload
from system.services.class_overview import get_registration_catalog_payload
from system.services.financial_transactions import resolve_checkout_action_for_plan
from system.services.membership import get_active_membership
from system.services.registration_checkout import (
    create_pre_registration_materials_payment,
    create_pre_registration_plan_payment,
    get_plan_catalog_payload,
    get_product_catalog_payload,
    resolve_catalog_plan,
)
from system.selectors.plan_eligibility import build_eligibility_context_for_person
from system.views.portal_mixins import PortalLoginRequiredMixin


@method_decorator(xframe_options_sameorigin, name="dispatch")
class DependentRegistrationView(PortalLoginRequiredMixin, TemplateView):
    template_name = "dependents/dependent_registration.html"
    done_template_name = "dependents/dependent_registration_done.html"

    def get(self, request, *args, **kwargs):
        if not self._is_modal_request():
            return redirect(self._home_modal_url())
        owner = self._get_owner()
        pending = get_pending_dependent_pre_registration(request.session, owner)
        initial = initial_from_pre_registration(pending)
        form = DependentRegistrationForm(
            owner=owner,
            pending=pending,
            initial=initial,
        )
        return self.render_to_response(self.get_context_data(form=form, pending=pending))

    def post(self, request, *args, **kwargs):
        owner = self._get_owner()
        pending = get_pending_dependent_pre_registration(request.session, owner)
        post_data = request.POST
        if self._payment_confirmed(pending):
            post_data = request.POST.copy()
            self._restore_confirmed_payment_post_data(post_data, pending)
        form = DependentRegistrationForm(
            post_data,
            owner=owner,
            pending=pending,
        )
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, pending=pending))

        if form.existing_owned_dependent is not None:
            request.session.pop("pending_dependent_pre_registration_id", None)
            messages.info(request, "Este dependente já está vinculado ao seu cadastro.")
            if self._is_modal_request():
                return self._render_modal_done(
                    "Este dependente já está vinculado ao seu cadastro."
                )
            return redirect("system:home")

        payment_confirmed = self._payment_confirmed(pending)
        materials_confirmed = self._materials_confirmed(pending)
        if payment_confirmed:
            pending_snapshot = (pending.form_snapshot or {}) if pending else {}
            financial_mode = (
                pending_snapshot.get("financial_mode")
                or DependentFinancialMode.DEPENDENT_OWN
            )
            form.cleaned_data["financial_mode"] = financial_mode
            form.cleaned_data["use_family_plan"] = (
                financial_mode == DependentFinancialMode.FAMILY_EXISTING
            )
            snapshot_plan_id = pending_snapshot.get("selected_plan") or ""
            if snapshot_plan_id:
                legacy_plan, plan_price = resolve_catalog_plan(snapshot_plan_id)
                form.cleaned_data["selected_plan"] = str(snapshot_plan_id)
                form.cleaned_data["selected_plan_obj"] = legacy_plan or plan_price
            elif pending and pending.selected_plan_id:
                form.cleaned_data["selected_plan"] = str(pending.selected_plan_id)
                form.cleaned_data["selected_plan_obj"] = pending.selected_plan
            if pending and pending.checkout_action:
                form.cleaned_data["checkout_action"] = pending.checkout_action

        selected_materials = form.cleaned_data.get("selected_product_items") or []
        if (
            (form.cleaned_data.get("use_family_plan") or payment_confirmed)
            and selected_materials
            and not materials_confirmed
        ):
            if request.session.session_key is None:
                request.session.save()
            if pending is None:
                pending = create_dependent_pre_registration(
                    owner,
                    form.cleaned_data,
                    session_key=request.session.session_key or "",
                )
            else:
                pending = update_dependent_pre_registration(
                    pending,
                    owner,
                    form.cleaned_data,
                )
            request.session["pending_dependent_pre_registration_id"] = pending.pk
            checkout_url = create_pre_registration_materials_payment(
                pending,
                selected_materials,
                form.cleaned_data["materials_checkout_action"],
            )
            save_checkout_url(pending, "materials", checkout_url)
            return redirect(checkout_url)

        if form.cleaned_data.get("use_family_plan") or payment_confirmed:
            finalize_dependent_registration(
                owner,
                form.cleaned_data,
                pre_registration=pending,
            )
            request.session.pop("pending_dependent_pre_registration_id", None)
            messages.success(request, "Dependente adicionado com sucesso.")
            if self._is_modal_request():
                return self._render_modal_done("Dependente adicionado com sucesso.")
            return redirect("system:home")

        checkout_action = form.cleaned_data.get("checkout_action")
        if not checkout_action or checkout_action == "pay_later":
            checkout_action = resolve_checkout_action_for_plan(
                form.cleaned_data.get("selected_plan_obj")
            )
        if checkout_action == "pay_later":
            form.add_error(
                "selected_plan",
                "Conclua o pagamento para finalizar o dependente.",
            )
            return self.render_to_response(self.get_context_data(form=form, pending=pending))

        if request.session.session_key is None:
            request.session.save()
        pre_registration = create_dependent_pre_registration(
            owner,
            form.cleaned_data,
            session_key=request.session.session_key or "",
        )
        request.session["pending_dependent_pre_registration_id"] = pre_registration.pk
        existing_checkout_url = (pre_registration.form_snapshot or {}).get(
            "plan_checkout_url"
        )
        if pre_registration.is_awaiting_payment and existing_checkout_url:
            return redirect(existing_checkout_url)
        checkout_url = create_pre_registration_plan_payment(
            pre_registration,
            checkout_action,
            card_strategy=form.cleaned_data.get("card_strategy"),
            owner=owner,
        )
        save_checkout_url(pre_registration, "plan", checkout_url)
        pre_registration.mark_awaiting_payment()
        return redirect(checkout_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = kwargs.get("pending")
        context["owner"] = self._get_owner()
        context["pending_pre_registration"] = pending
        context["payment_confirmed"] = self._payment_confirmed(pending)
        context["materials_confirmed"] = self._materials_confirmed(pending)
        context["family_plan_selected"] = self._family_plan_selected(context["form"])
        context["family_plan_available"] = getattr(
            context["form"], "family_plan_available", False
        )
        context["material_groups"] = self._build_material_groups(context["form"])
        context["is_modal"] = self._is_modal_request()
        context["class_catalog_json"] = json.dumps(
            get_registration_catalog_payload(), ensure_ascii=False
        )
        context["plan_catalog_json"] = json.dumps(
            get_plan_catalog_payload(include_plan_prices=True), ensure_ascii=False
        )
        context["product_catalog_json"] = json.dumps(
            get_product_catalog_payload(), ensure_ascii=False
        )
        context["owner_plan_context_json"] = json.dumps(
            self._build_owner_plan_context(context["owner"]),
            ensure_ascii=False,
        )
        context["ibjjf_categories_json"] = json.dumps(
            get_ibjjf_age_category_payload(), ensure_ascii=False
        )
        return context

    def _restore_confirmed_payment_post_data(self, post_data, pending):
        snapshot = (pending.form_snapshot or {}) if pending else {}
        financial_mode = (
            snapshot.get("financial_mode") or DependentFinancialMode.DEPENDENT_OWN
        )
        post_data["financial_mode"] = financial_mode
        if financial_mode == DependentFinancialMode.FAMILY_EXISTING:
            post_data["use_family_plan"] = "on"
        elif "use_family_plan" in post_data:
            del post_data["use_family_plan"]

        selected_plan_id = ""
        if snapshot.get("selected_plan"):
            selected_plan_id = str(snapshot.get("selected_plan"))
        elif pending and pending.selected_plan_id:
            from system.services.registration_checkout import (
                CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
                build_catalog_plan_id,
            )

            selected_plan_id = build_catalog_plan_id(
                CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, pending.selected_plan_id
            )
        if selected_plan_id:
            post_data["selected_plan"] = selected_plan_id

        checkout_action = ""
        if pending and pending.checkout_action:
            checkout_action = pending.checkout_action
        elif snapshot.get("checkout_action"):
            checkout_action = snapshot.get("checkout_action")
        if checkout_action:
            post_data["checkout_action"] = checkout_action

    def _build_owner_plan_context(self, owner):
        eligibility = build_eligibility_context_for_person(owner)
        owner_membership = get_active_membership(owner)
        return {
            "adult_active": eligibility.adult_active,
            "adult_active_count": eligibility.resolved_adult_active_count,
            "kids_juvenile_active_count": eligibility.kids_juvenile_active_count,
            "veteran_eligible": eligibility.veteran_eligible,
            "owner_has_stripe_subscription": bool(
                owner_membership and owner_membership.stripe_subscription_id
            ),
        }

    def _is_modal_request(self):
        return (
            self.request.GET.get("modal") == "1"
            or self.request.POST.get("_modal") == "1"
        )

    def _home_modal_url(self):
        return f"{reverse('system:home')}?dependent_modal=1"

    def _render_modal_done(self, message):
        return render(
            self.request,
            self.done_template_name,
            {
                "message": message,
            },
        )

    def _get_owner(self):
        owner = getattr(self.request, "portal_person", None)
        if owner is None:
            raise PermissionDenied("Cadastro de dependente exige uma pessoa de portal.")
        return owner

    def _payment_confirmed(self, pre_registration):
        if pre_registration is None:
            return False
        snapshot = pre_registration.form_snapshot or {}
        return pre_registration.payment_confirmed or bool(snapshot.get("plan_paid"))

    def _materials_confirmed(self, pre_registration):
        if pre_registration is None:
            return False
        snapshot = pre_registration.form_snapshot or {}
        return bool(snapshot.get("materials_paid"))

    def _family_plan_selected(self, form):
        value = form["use_family_plan"].value()
        return value in (True, "on", "true", "True", "1")

    def _build_material_groups(self, form):
        groups = []
        group_by_category = {}
        for variant in getattr(form, "material_variants", []):
            category = variant.product.category
            group = group_by_category.get(category.pk)
            if group is None:
                group = {
                    "category": category,
                    "products": {},
                }
                group_by_category[category.pk] = group
                groups.append(group)
            product = group["products"].get(variant.product_id)
            if product is None:
                product = {
                    "product": variant.product,
                    "variants": [],
                }
                group["products"][variant.product_id] = product
            field_name = f"material_variant_{variant.pk}"
            product["variants"].append(
                {
                    "variant": variant,
                    "field": form[field_name],
                }
            )
        for group in groups:
            group["products"] = list(group["products"].values())
        return groups


class DependentProfileUpdateView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        owner = getattr(request, "portal_person", None)
        if owner is None:
            return JsonResponse({"success": False, "error": "Não autenticado."}, status=403)

        relationship = get_object_or_404(
            PersonRelationship.objects.select_related("target_person"),
            source_person=owner,
            target_person_id=kwargs["pk"],
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        dependent = relationship.target_person
        form = DependentProfileForm(request.POST, instance=dependent)
        if not form.is_valid():
            return JsonResponse(
                {"success": False, "errors": _dependent_form_errors(form)},
                status=400,
            )

        updated_dependent = form.save()
        record_audit_event(
            module=AuditModule.PERSON,
            action=AuditAction.UPDATE,
            actor_label=owner.full_name,
            entity_label=updated_dependent.full_name,
            summary=f"Cadastro do dependente atualizado por {owner.full_name}.",
        )
        return JsonResponse({
            "success": True,
            "message": "Cadastro atualizado.",
            "person": _dependent_profile_payload(updated_dependent),
        })


def _dependent_form_errors(form):
    errors = {}
    for field_name, error_list in form.errors.items():
        errors[field_name] = [str(error) for error in error_list]
    return errors


def _dependent_profile_payload(person):
    return {
        "full_name": person.full_name,
        "initial": (person.full_name[:1] or "").upper(),
        "cpf": person.cpf or "",
        "email": person.email or "",
        "phone": person.phone or "",
        "birth_date": date_format(person.birth_date, "SHORT_DATE_FORMAT") if person.birth_date else "",
    }


class DependentRemoveView(PortalLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        owner = getattr(request, "portal_person", None)
        if owner is None:
            raise PermissionDenied("Remoção de dependente exige uma pessoa de portal.")
        relationship = get_object_or_404(
            PersonRelationship.objects.select_related("target_person"),
            source_person=owner,
            target_person_id=kwargs["pk"],
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        dependent = relationship.target_person
        dependent_name = dependent.full_name

        from system.models.membership import MembershipStatus
        from system.services.plan_change import get_plan_change_lock

        dependent_membership = (
            dependent.memberships.exclude(
                status__in=(MembershipStatus.CANCELED, MembershipStatus.EXPIRED)
            )
            .order_by("-created_at")
            .first()
        )
        lock = get_plan_change_lock(dependent_membership)
        if lock["is_locked"]:
            messages.error(
                request,
                f"{dependent_name} não pode ser removido agora: {lock['message']}",
            )
            return redirect("system:home")

        relationship.delete()

        from system.services.family_pricing import recompute_family_discounts_for_person

        recompute_family_discounts_for_person(owner)
        recompute_family_discounts_for_person(dependent)

        messages.success(
            request,
            f"{dependent_name} foi removido dos seus dependentes.",
        )
        return redirect("system:home")
