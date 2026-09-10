from django.db.models import Count, Prefetch
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from system.business_rule.forms import PersonTypeForm
from system.business_rule.models import Person, PersonType
from system.business_rule.access import AdministrativeRequiredMixin
from system.business_rule.views.person_views.modal import ModalFormMixin


class PersonTypeListView(AdministrativeRequiredMixin, ListView):
    model = PersonType
    template_name = "business_rule/person_types/person_type_list.html"
    context_object_name = "person_types"

    def get_queryset(self):
        return PersonType.objects.annotate(people_count=Count("people")).order_by(
            "display_name"
        )


class PersonTypeCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "business_rule/person_types/person_type_form.html"
    modal_name = "person-type-create"
    success_url = reverse_lazy("system:person-type-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Novo perfil"
        return context


class PersonTypeUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "business_rule/person_types/person_type_form.html"
    modal_name = "person-type-edit"
    success_url = reverse_lazy("system:person-type-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar perfil"
        return context


class PersonTypeDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = PersonType
    template_name = "business_rule/person_types/person_type_confirm_delete.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeDetailView(AdministrativeRequiredMixin, DetailView):
    model = PersonType
    template_name = "business_rule/person_types/person_type_detail.html"
    context_object_name = "person_type"

    def get_queryset(self):
        return PersonType.objects.prefetch_related(
            Prefetch(
                "people",
                queryset=Person.objects.order_by("full_name"),
            )
        )
