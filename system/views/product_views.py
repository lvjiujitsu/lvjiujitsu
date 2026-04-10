from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms.product_forms import ProductForm, get_product_variant_formset
from system.models.product import Product
from system.services.product_management import (
    get_product_card_by_pk,
    get_product_list_cards,
    get_public_product_cards,
    save_product_with_variants,
)
from system.views.person_views import AdministrativeRequiredMixin


class ProductVariantMixin:
    def get_variant_formset(self):
        data = self.request.POST if self.request.method == "POST" else None
        return get_product_variant_formset(
            data=data,
            instance=getattr(self, "object", None),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["variant_formset"] = kwargs.get("variant_formset") or self.get_variant_formset()
        return ctx

    def form_valid(self, form):
        variant_formset = self.get_variant_formset()
        if not variant_formset.is_valid():
            return self.form_invalid(form, variant_formset)
        self.object = save_product_with_variants(
            form=form,
            variant_formset=variant_formset,
        )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, variant_formset=None):
        fs = variant_formset or self.get_variant_formset()
        return self.render_to_response(
            self.get_context_data(form=form, variant_formset=fs),
        )


class ProductListView(AdministrativeRequiredMixin, ListView):
    template_name = "products/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return get_product_list_cards()


class ProductCreateView(AdministrativeRequiredMixin, ProductVariantMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    success_url = reverse_lazy("system:product-list")


class ProductDetailView(AdministrativeRequiredMixin, DetailView):
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        return get_product_card_by_pk(self.kwargs["pk"])


class ProductUpdateView(AdministrativeRequiredMixin, ProductVariantMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"

    def get_success_url(self):
        return reverse_lazy("system:product-detail", kwargs={"pk": self.object.pk})


class ProductDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy("system:product-list")
    context_object_name = "product"


class ProductCatalogView(ListView):
    template_name = "products/product_catalog.html"
    context_object_name = "products"

    def get_queryset(self):
        return get_public_product_cards()
