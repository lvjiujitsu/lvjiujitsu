from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from system.forms import ClassCategoryForm
from system.models import ClassCategory
from system.views.person_views import AdministrativeRequiredMixin


class ClassCategoryListView(AdministrativeRequiredMixin, ListView):
    model = ClassCategory
    template_name = "class_categories/class_category_list.html"
    context_object_name = "class_categories"

    def get_queryset(self):
        return ClassCategory.objects.order_by("display_order", "display_name")


class ClassCategoryCreateView(AdministrativeRequiredMixin, CreateView):
    model = ClassCategory
    form_class = ClassCategoryForm
    template_name = "class_categories/class_category_form.html"
    success_url = reverse_lazy("system:class-category-list")


class ClassCategoryUpdateView(AdministrativeRequiredMixin, UpdateView):
    model = ClassCategory
    form_class = ClassCategoryForm
    template_name = "class_categories/class_category_form.html"
    success_url = reverse_lazy("system:class-category-list")


class ClassCategoryDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = ClassCategory
    template_name = "class_categories/class_category_confirm_delete.html"
    success_url = reverse_lazy("system:class-category-list")
