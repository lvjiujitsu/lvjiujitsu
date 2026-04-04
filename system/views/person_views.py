from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from system.forms import PersonForm, PersonTypeForm
from system.models import Person, PersonType


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class PersonListView(StaffRequiredMixin, ListView):
    model = Person
    template_name = "people/person_list.html"
    context_object_name = "people"

    def get_queryset(self):
        return Person.objects.prefetch_related("person_types").select_related("user")


class PersonCreateView(StaffRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    success_url = reverse_lazy("system:person-list")


class PersonUpdateView(StaffRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "people/person_form.html"
    success_url = reverse_lazy("system:person-list")


class PersonDeleteView(StaffRequiredMixin, DeleteView):
    model = Person
    template_name = "people/person_confirm_delete.html"
    success_url = reverse_lazy("system:person-list")


class PersonTypeListView(StaffRequiredMixin, ListView):
    model = PersonType
    template_name = "person_types/person_type_list.html"
    context_object_name = "person_types"


class PersonTypeCreateView(StaffRequiredMixin, CreateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeUpdateView(StaffRequiredMixin, UpdateView):
    model = PersonType
    form_class = PersonTypeForm
    template_name = "person_types/person_type_form.html"
    success_url = reverse_lazy("system:person-type-list")


class PersonTypeDeleteView(StaffRequiredMixin, DeleteView):
    model = PersonType
    template_name = "person_types/person_type_confirm_delete.html"
    success_url = reverse_lazy("system:person-type-list")
