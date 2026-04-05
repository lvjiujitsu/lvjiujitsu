from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from system.forms import PersonForm, PersonTypeForm
from system.models import IbjjfAgeCategory, Person, PersonType
from system.views.portal_mixins import PortalRoleRequiredMixin


class AdministrativeRequiredMixin(PortalRoleRequiredMixin):
    allowed_codes = ("administrative-assistant",)


class PersonListView(AdministrativeRequiredMixin, ListView):
    model = Person
    template_name = "people/person_list.html"
    context_object_name = "people"

    def get_queryset(self):
        return (
            Person.objects.select_related(
                "access_account",
                "person_type",
                "class_category",
                "class_group",
                "class_schedule",
            )
            .order_by("full_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_ibjjf_categories = list(
            IbjjfAgeCategory.objects.filter(is_active=True).order_by(
                "display_order",
                "minimum_age",
            )
        )
        for person in context["people"]:
            person.resolved_ibjjf_category = next(
                (
                    category
                    for category in active_ibjjf_categories
                    if person.get_age() is not None and category.matches_age(person.get_age())
                ),
                None,
            )
        return context


class PersonCreateView(AdministrativeRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    success_url = reverse_lazy("system:person-list")


class PersonUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    success_url = reverse_lazy("system:person-list")


class PersonDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Person
    template_name = "people/person_confirm_delete.html"
    success_url = reverse_lazy("system:person-list")


class PersonTypeListView(AdministrativeRequiredMixin, ListView):
    model = PersonType
    template_name = "person_types/person_type_list.html"
    context_object_name = "person_types"


class PersonTypeCreateView(AdministrativeRequiredMixin, CreateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = PersonType
    template_name = "person_types/person_type_confirm_delete.html"
    success_url = reverse_lazy("system:person-type-list")
