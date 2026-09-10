from django.conf import settings
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from system.core.audit import AuditAction
from system.business_rule.forms import PersonForm, PersonListFilterForm
from system.business_rule.constants import AuditModule
from system.business_rule.models import Graduation, IbjjfAgeCategory, Person
from system.business_rule.models.membership import Membership, MembershipInvoice
from system.business_rule.models.plan import SubscriptionPlan
from system.business_rule.models.registration_order import PaymentStatus, RegistrationOrder
from system.business_rule.selectors import (
    compute_veteran_member_since,
    get_person_queryset,
    is_veteran_plan_eligible,
)
from system.business_rule.services.access_requests import get_administrative_access_requests_for_person
from system.core.audit import record_event
from system.business_rule.services.class_requests import get_class_catalog_requests_history_for_person
from system.business_rule.services.graduation import compute_graduation_progress, get_graduation_history
from system.business_rule.services.membership import get_active_membership, get_membership_owner
from system.business_rule.services.veteran_plan import approve_veteran_plan, revoke_veteran_plan
from system.business_rule.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES, Capability
from system.business_rule.access import (
    AdministrativeRequiredMixin,
    PortalRoleRequiredMixin,
    portal_person,
)
from system.business_rule.views.person_views.access import PeopleSupportRequiredMixin, can_manage_people
from system.business_rule.views.person_views.detail_context import compute_belt_stripes, format_person_delete_blockers, hydrate_person_relationships
from system.business_rule.views.person_views.modal import ModalCrudMixin, ModalFormMixin


class PersonListView(PeopleSupportRequiredMixin, ListView):
    model = Person
    template_name = "business_rule/people/person_list.html"
    context_object_name = "people"

    def dispatch(self, request, *args, **kwargs):
        self.filter_form = PersonListFilterForm(request.GET or None)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.filter_form.is_valid():
            queryset = get_person_queryset(filters=self.filter_form.cleaned_data)
        else:
            queryset = get_person_queryset()
        if not can_manage_people(self.request):
            queryset = queryset.filter(
                person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["can_manage_people"] = can_manage_people(self.request)
        context["person_create_label"] = (
            "Nova pessoa" if context["can_manage_people"] else "Cadastrar aluno"
        )
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        people = list(context["people"])
        context["people"] = people
        for person in people:
            hydrate_person_relationships(person, active_ibjjf_categories)
        return context


class PersonCreateView(ModalFormMixin, PeopleSupportRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "business_rule/people/person_form.html"
    modal_template_name = "business_rule/people/person_form_modal.html"
    modal_name = "person-create"
    success_url = reverse_lazy("system:person-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not can_manage_people(self.request):
            kwargs["person_type_codes"] = CLASS_ENROLLMENT_PERSON_TYPE_CODES
            kwargs["show_payroll_fields"] = False
            kwargs["show_operational_role_fields"] = False
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        record_event(
            self.request,
            AuditAction.CREATED,
            AuditModule.PERSON,
            self.object.full_name,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_people"] = can_manage_people(self.request)
        return context


class PersonUpdateView(ModalFormMixin, PeopleSupportRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "business_rule/people/person_form.html"
    modal_template_name = "business_rule/people/person_form_modal.html"
    modal_name = "person-edit"
    success_url = reverse_lazy("system:person-list")

    def get_queryset(self):
        queryset = get_person_queryset()
        if not can_manage_people(self.request):
            queryset = queryset.filter(
                person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES
            )
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not can_manage_people(self.request):
            kwargs["person_type_codes"] = CLASS_ENROLLMENT_PERSON_TYPE_CODES
            kwargs["show_payroll_fields"] = False
            kwargs["show_operational_role_fields"] = False
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        record_event(
            self.request,
            AuditAction.UPDATED,
            AuditModule.PERSON,
            self.object.full_name,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_people"] = can_manage_people(self.request)
        person = context["object"]
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        hydrate_person_relationships(person, active_ibjjf_categories)
        context["graduation_progress"] = compute_graduation_progress(person)
        context["graduation_history"] = get_graduation_history(person)
        context["has_official_graduation"] = Graduation.objects.filter(
            person=person
        ).exists()
        return context


class PersonDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Person
    template_name = "business_rule/people/person_confirm_delete.html"
    success_url = reverse_lazy("system:person-list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError as error:
            blockers = format_person_delete_blockers(error.protected_objects)
            messages.error(
                self.request,
                (
                    f"Não foi possível excluir {self.object.full_name} porque há "
                    f"vínculo protegido em {blockers}. Remova ou substitua esse "
                    "vínculo antes de excluir."
                ),
            )
            return redirect("system:person-detail", pk=self.object.pk)
        record_event(
            self.request,
            AuditAction.DELETED,
            AuditModule.PERSON,
            self.object.full_name,
        )
        messages.success(
            self.request,
            f"{self.object.full_name} foi excluído(a) com sucesso.",
        )
        return HttpResponseRedirect(success_url)


class PersonDetailView(ModalCrudMixin, PeopleSupportRequiredMixin, DetailView):
    model = Person
    template_name = "business_rule/people/person_detail.html"
    modal_template_name = "business_rule/people/person_detail_modal.html"
    modal_name = "person-view"
    context_object_name = "person"

    def get_queryset(self):
        queryset = get_person_queryset()
        if not can_manage_people(self.request):
            queryset = queryset.filter(
                person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_people"] = can_manage_people(self.request)
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        hydrate_person_relationships(context["person"], active_ibjjf_categories)
        context["graduation_progress"] = compute_graduation_progress(context["person"])
        context["graduation_history"] = get_graduation_history(context["person"])
        context["belt_stripes_detail"] = compute_belt_stripes(context["graduation_progress"])
        if not context["can_manage_people"]:
            return context
        person = context["person"]
        context["access_request_history"] = get_administrative_access_requests_for_person(
            person, limit=20
        )
        context["class_request_history"] = get_class_catalog_requests_history_for_person(
            person, limit=20
        )
        billing_person = get_membership_owner(person)
        memberships = list(
            Membership.objects.filter(person=billing_person)
            .select_related("plan")
            .order_by("-created_at")
        )
        context["memberships"] = memberships
        active_membership = get_active_membership(person)
        context["active_membership"] = active_membership
        context["billing_owner"] = billing_person
        if active_membership is not None:
            context["person_invoices"] = list(
                MembershipInvoice.objects.filter(membership=active_membership)
                .order_by("-paid_at", "-created_at")[:10]
            )
        else:
            context["person_invoices"] = []
        context["person_orders"] = list(
            RegistrationOrder.objects.filter(person=billing_person)
            .select_related("plan")
            .order_by("-created_at")[:15]
        )
        context["pending_orders"] = [
            o for o in context["person_orders"]
            if o.payment_status not in (
                PaymentStatus.PAID,
                PaymentStatus.EXEMPTED,
                PaymentStatus.REFUNDED,
            )
        ]
        context["available_plans"] = list(
            SubscriptionPlan.objects.filter(is_active=True).order_by("display_name")
        )
        context["veteran_plan_owner"] = billing_person
        context["veteran_member_since"] = compute_veteran_member_since(billing_person)
        context["veteran_plan_eligible"] = is_veteran_plan_eligible(billing_person)
        context["veteran_plan_tenure_years"] = settings.VETERAN_PLAN_TENURE_YEARS
        return context


class VeteranPlanDecisionView(PortalRoleRequiredMixin, View):
    required_capabilities = (Capability.MANAGE_PEOPLE, Capability.MANAGE_ACADEMY)

    def post(self, request, pk, *args, **kwargs):
        person = get_object_or_404(Person, pk=pk)
        action = request.POST.get("action")
        notes = request.POST.get("notes", "")
        actor = portal_person(request)
        if action == "revoke":
            revoke_veteran_plan(person, revoked_by=actor, notes=notes)
            messages.success(request, "Plano Veterano revogado.")
        else:
            approve_veteran_plan(person, approved_by=actor, notes=notes)
            messages.success(request, "Plano Veterano aprovado.")
        return redirect("system:person-detail", pk=person.pk)
