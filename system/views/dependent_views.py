from urllib.parse import quote

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views import View
from django.views.generic import TemplateView

from system.forms import DependentProfileForm, DependentRegistrationForm
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.services.dependent_registration import (
    create_dependent_pre_registration,
    finalize_dependent_registration,
    get_pending_dependent_pre_registration,
    initial_from_pre_registration,
    save_checkout_url,
    update_dependent_pre_registration,
)
from system.services.financial_transactions import resolve_checkout_action_for_plan
from system.services.registration_checkout import (
    create_pre_registration_materials_payment,
    create_pre_registration_plan_payment,
)
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
        form = DependentRegistrationForm(
            request.POST,
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
            form.cleaned_data["use_family_plan"] = False
            if pending and pending.selected_plan_id:
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
        context["material_groups"] = self._build_material_groups(context["form"])
        context["is_modal"] = self._is_modal_request()
        return context

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


@method_decorator(xframe_options_sameorigin, name="dispatch")
class DependentUpdateView(PortalLoginRequiredMixin, TemplateView):
    template_name = "dependents/dependent_edit.html"
    done_template_name = "dependents/dependent_registration_done.html"

    def get(self, request, *args, **kwargs):
        if not self._is_modal_request():
            return redirect(self._home_modal_url())
        relationship = self._get_relationship()
        form = DependentProfileForm(instance=relationship.target_person)
        return self.render_to_response(
            self.get_context_data(form=form, dependent=relationship.target_person)
        )

    def post(self, request, *args, **kwargs):
        relationship = self._get_relationship()
        form = DependentProfileForm(request.POST, instance=relationship.target_person)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, dependent=relationship.target_person)
            )
        form.save()
        messages.success(request, "Dependente atualizado com sucesso.")
        if self._is_modal_request():
            return self._render_modal_done("Dependente atualizado com sucesso.")
        return redirect("system:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self._get_owner()
        context["is_modal"] = self._is_modal_request()
        return context

    def _get_relationship(self):
        owner = self._get_owner()
        return get_object_or_404(
            PersonRelationship.objects.select_related("target_person"),
            source_person=owner,
            target_person_id=self.kwargs["pk"],
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

    def _get_owner(self):
        owner = getattr(self.request, "portal_person", None)
        if owner is None:
            raise PermissionDenied("Edição de dependente exige uma pessoa de portal.")
        return owner

    def _is_modal_request(self):
        return (
            self.request.GET.get("modal") == "1"
            or self.request.POST.get("_modal") == "1"
        )

    def _home_modal_url(self):
        edit_url = f"{reverse('system:dependent-edit', args=[self.kwargs['pk']])}?modal=1"
        return (
            f"{reverse('system:home')}?dependent_modal=1"
            f"&dependent_modal_url={quote(edit_url, safe='')}"
        )

    def _render_modal_done(self, message):
        return render(
            self.request,
            self.done_template_name,
            {
                "message": message,
            },
        )


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
        dependent_name = relationship.target_person.full_name
        relationship.delete()
        messages.success(
            request,
            f"{dependent_name} foi removido dos seus dependentes.",
        )
        return redirect("system:home")
