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

from system.core.forms import form_error_payload
from system.core.audit import AuditAction
from system.business_rule.forms import DependentProfileForm, DependentRegistrationForm
from system.business_rule.constants import AuditModule
from system.business_rule.models.person import PersonRelationship, PersonRelationshipKind
from system.core.audit import record_event
from system.business_rule.services.asaas_client import AsaasClientError
from system.business_rule.services.dependent_registration import (
    find_dependent_pre_registration,
    get_pending_dependent_pre_registration,
    initial_from_pre_registration,
    is_dependent_materials_confirmed,
    is_dependent_payment_confirmed,
    process_dependent_registration_submission,
    restore_confirmed_payment_post_data,
)
from system.business_rule.services.class_catalog import get_ibjjf_age_category_payload
from system.business_rule.services.class_overview import get_registration_catalog_payload
from system.business_rule.services.membership import get_active_membership
from system.business_rule.services.registration_checkout import (
    get_product_catalog_payload,
    get_public_registration_plan_catalog_payload,
)
from system.business_rule.selectors.plan_eligibility import build_eligibility_context_for_person
from system.core.documents import ensure_formatted_cpf
from system.business_rule.access import (
    PortalLoginRequiredMixin,
    portal_person,
)
from system.business_rule.services.plan_change import get_plan_change_lock
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.services.family_pricing import recompute_family_discounts_for_person
from system.business_rule.models.membership_timeline import MembershipTimelineEventType
from system.business_rule.models.membership import MembershipStatus


@method_decorator(xframe_options_sameorigin, name="dispatch")
class DependentRegistrationView(PortalLoginRequiredMixin, TemplateView):
    template_name = "business_rule/dependents/dependent_registration.html"
    done_template_name = "business_rule/dependents/dependent_registration_done.html"

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
        if pending is None:
            pending = self._recover_pending(request, owner)
        post_data = request.POST
        if is_dependent_payment_confirmed(pending):
            post_data = request.POST.copy()
            restore_confirmed_payment_post_data(post_data, pending)
        form = DependentRegistrationForm(
            post_data,
            owner=owner,
            pending=pending,
        )
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, pending=pending))

        try:
            result = process_dependent_registration_submission(
                owner=owner, form=form, pending=pending, session=request.session,
            )
        except (AsaasClientError, ValueError) as exc:
            form.add_error(None, _dependent_checkout_error_message(exc))
            return self.render_to_response(
                self.get_context_data(form=form, pending=pending)
            )
        return self._respond_to_submission_result(request, result, form, pending)

    def _recover_pending(self, request, owner):
        try:
            dependent_cpf = ensure_formatted_cpf(
                request.POST.get("dependent_cpf") or ""
            )
        except ValueError:
            return None
        pending = find_dependent_pre_registration(owner, dependent_cpf)
        if pending is not None and pending.session_key != (request.session.session_key or ""):
            return None
        if pending is not None:
            request.session["pending_dependent_pre_registration_id"] = pending.pk
        return pending

    def _respond_to_submission_result(self, request, result, form, pending):
        kind = result["kind"]
        if kind == "existing_owned":
            messages.info(request, "Este dependente já está vinculado ao seu cadastro.")
            if self._is_modal_request():
                return self._render_modal_done(
                    "Este dependente já está vinculado ao seu cadastro."
                )
            return redirect("system:home")

        if kind == "materials_checkout" or kind == "plan_checkout":
            return redirect(result["checkout_url"])

        if kind == "finalized":
            messages.success(request, "Dependente adicionado com sucesso.")
            if self._is_modal_request():
                return self._render_modal_done("Dependente adicionado com sucesso.")
            return redirect("system:home")

        form.add_error("selected_plan", "Conclua o pagamento para finalizar o dependente.")
        return self.render_to_response(self.get_context_data(form=form, pending=pending))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = kwargs.get("pending")
        context["owner"] = self._get_owner()
        context["pending_pre_registration"] = pending
        context["payment_confirmed"] = is_dependent_payment_confirmed(pending)
        context["materials_confirmed"] = is_dependent_materials_confirmed(pending)
        context["family_plan_selected"] = self._family_plan_selected(context["form"])
        context["family_plan_available"] = getattr(
            context["form"], "family_plan_available", False
        )
        context["material_groups"] = self._build_material_groups(context["form"])
        context["is_modal"] = self._is_modal_request()
        context["class_catalog_json"] = get_registration_catalog_payload()
        context["plan_catalog_json"] = get_public_registration_plan_catalog_payload()
        context["product_catalog_json"] = get_product_catalog_payload()
        context["owner_plan_context_json"] = self._build_owner_plan_context(context["owner"])
        context["ibjjf_categories_json"] = get_ibjjf_age_category_payload()
        return context

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
        owner = portal_person(self.request)
        if owner is None:
            raise PermissionDenied("Cadastro de dependente exige uma pessoa de portal.")
        return owner

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
        owner = portal_person(request)
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
                {"success": False, "errors": form_error_payload(form)},
                status=400,
            )

        updated_dependent = form.save()
        record_event(
            owner.full_name,
            AuditAction.UPDATED,
            AuditModule.PERSON,
            updated_dependent.full_name,
            f"Cadastro do dependente atualizado por {owner.full_name}.",
        )
        return JsonResponse({
            "success": True,
            "message": "Cadastro atualizado.",
            "person": _dependent_profile_payload(updated_dependent),
        })


def _dependent_checkout_error_message(error):
    if isinstance(error, AsaasClientError):
        payload = error.payload if isinstance(error.payload, dict) else {}
        errors = payload.get("errors") or []
        if errors and isinstance(errors[0], dict):
            description = errors[0].get("description")
            if description:
                return description
        return "Não foi possível iniciar o pagamento no Asaas. Tente novamente."
    return str(error)


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
        owner = portal_person(request)
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


        record_membership_event(
            owner,
            MembershipTimelineEventType.DEPENDENT_REMOVED,
            actor=owner,
            context={"dependent_name": dependent_name},
        )
        record_membership_event(
            dependent,
            MembershipTimelineEventType.DEPENDENT_REMOVED,
            actor=owner,
            context={"dependent_name": dependent_name},
        )

        recompute_family_discounts_for_person(owner)
        recompute_family_discounts_for_person(dependent)

        messages.success(
            request,
            f"{dependent_name} foi removido dos seus dependentes.",
        )
        return redirect("system:home")
