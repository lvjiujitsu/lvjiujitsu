import json
from collections import OrderedDict

from django.contrib import messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from system.forms.product_forms import (
    ProductCartForm,
    ProductCategoryForm,
    ProductForm,
    get_product_variant_formset,
)
from system.models.product import Product, ProductCategory, ProductVariant
from system.models.product_backorder import ProductBackorder
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.constants import MATERIAL_REQUEST_PERSON_TYPE_CODES
from system.models import Person
from system.selectors.product_backorders import (
    get_admin_backorder_queue,
    get_backorders_for_person,
)
from system.selectors.person_selectors import (
    get_material_request_recipient_queryset,
    resolve_material_request_recipient,
)
from system.services.product_backorders import (
    ProductBackorderError,
    cancel_backorder,
    confirm_backorder,
    create_backorder,
)
from system.services.product_management import (
    get_product_card_by_pk,
    get_product_list_cards,
    get_public_product_cards,
    save_product_with_variants,
)
from system.services.registration_checkout import (
    create_product_only_order,
    get_product_catalog_payload,
)
from system.views.person_views import ModalFormMixin
from system.views.portal_mixins import AdministrativeRequiredMixin, PortalRoleRequiredMixin


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


class ProductCreateView(
    ModalFormMixin, AdministrativeRequiredMixin, ProductVariantMixin, CreateView
):
    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    modal_name = "product-create"
    success_url = reverse_lazy("system:product-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Novo material"
        return context


class ProductDetailView(AdministrativeRequiredMixin, DetailView):
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        return get_product_card_by_pk(self.kwargs["pk"])


class ProductUpdateView(
    ModalFormMixin, AdministrativeRequiredMixin, ProductVariantMixin, UpdateView
):
    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    modal_name = "product-edit"

    def get_success_url(self):
        return reverse_lazy("system:product-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar material"
        return context


class ProductDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy("system:product-list")
    context_object_name = "product"


class ProductStoreView(PortalRoleRequiredMixin, ListView):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES
    template_name = "products/product_store.html"
    context_object_name = "products"

    def get_queryset(self):
        return get_public_product_cards()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product_groups"] = _build_product_groups(context["products"])
        context["product_catalog_json"] = json.dumps(
            get_product_catalog_payload(),
            ensure_ascii=False,
        )
        context["out_of_stock_variants"] = self._build_out_of_stock_variants()
        context["purchase_person_choices"] = self._build_purchase_person_choices()
        context["purchase_person_default"] = getattr(self.request, "portal_person", None)
        return context

    def _build_out_of_stock_variants(self):
        from system.selectors.product_backorders import has_active_backorder_for_variant

        person = self.request.portal_person
        variants = (
            ProductVariant.objects.filter(
                is_active=True,
                stock_quantity=0,
                product__is_active=True,
                product__category__is_active=True,
            )
            .select_related("product", "product__category")
            .order_by("product__display_name", "color", "size")
        )
        rows = []
        for variant in variants:
            rows.append(
                {
                    "variant": variant,
                    "already_requested": has_active_backorder_for_variant(person, variant),
                }
            )
        return rows

    def _build_purchase_person_choices(self):
        actor = getattr(self.request, "portal_person", None)
        if actor is None and getattr(self.request, "portal_is_technical_admin", False):
            return list(
                Person.objects.select_related("person_type")
                .filter(
                    is_active=True,
                    person_type__is_active=True,
                    person_type__code__in=MATERIAL_REQUEST_PERSON_TYPE_CODES,
                )
                .order_by("full_name")
            )
        people = list(get_material_request_recipient_queryset(actor))
        return sorted(
            people,
            key=lambda person: (
                0 if actor is not None and person.pk == actor.pk else 1,
                person.full_name,
            ),
        )


class CreateProductOrderView(PortalRoleRequiredMixin, View):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES

    def post(self, request):
        form = ProductCartForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Carrinho inválido.")
            return redirect("system:product-store")

        person = _resolve_purchase_person_or_message(request)
        if person is None:
            return redirect("system:product-store")
        order = create_product_only_order(person, form.cleaned_data["cart_payload"])
        if order is None:
            messages.error(request, "Nenhum produto válido selecionado.")
            return redirect("system:product-store")

        request.session["pending_checkout_order_id"] = order.pk
        return redirect("system:payment-checkout", order_id=order.pk)


class ProductBackorderCreateView(PortalRoleRequiredMixin, View):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES

    def post(self, request):
        try:
            variant_id = int(request.POST.get("variant_id") or 0)
        except (TypeError, ValueError):
            variant_id = 0
        if variant_id <= 0:
            messages.error(request, "Selecione uma variante válida.")
            return redirect("system:product-store")

        variant = get_object_or_404(
            ProductVariant.objects.select_related("product"),
            pk=variant_id,
            is_active=True,
            product__is_active=True,
        )
        person = _resolve_purchase_person_or_message(request)
        if person is None:
            return redirect("system:product-store")
        try:
            create_backorder(person, variant)
        except ProductBackorderError as exc:
            messages.error(request, str(exc))
            return redirect("system:product-store")

        messages.success(
            request,
            "Pré-pedido registrado. Avisaremos quando o produto estiver disponível.",
        )
        return redirect("system:student-backorders")


class StudentBackorderListView(PortalRoleRequiredMixin, ListView):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES
    template_name = "products/student_backorder_list.html"
    context_object_name = "backorders"

    def get_queryset(self):
        recipients = get_material_request_recipient_queryset(self.request.portal_person)
        return get_backorders_for_person(recipients)


class StudentBackorderConfirmView(PortalRoleRequiredMixin, View):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES

    def post(self, request, pk):
        backorder = get_object_or_404(
            ProductBackorder.objects.select_related("variant", "variant__product"),
            pk=pk,
            person=request.portal_person,
        )
        try:
            order = confirm_backorder(backorder)
        except ProductBackorderError as exc:
            messages.error(request, str(exc))
            return redirect("system:student-backorders")

        return redirect("system:payment-checkout", order_id=order.pk)


class StudentBackorderCancelView(PortalRoleRequiredMixin, View):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES

    def post(self, request, pk):
        backorder = get_object_or_404(
            ProductBackorder,
            pk=pk,
            person=request.portal_person,
        )
        try:
            cancel_backorder(backorder)
        except ProductBackorderError as exc:
            messages.error(request, str(exc))
        else:
            messages.info(request, "Pré-pedido cancelado.")
        return redirect("system:student-backorders")


class StudentOrderHistoryView(PortalRoleRequiredMixin, ListView):
    allowed_codes = MATERIAL_REQUEST_PERSON_TYPE_CODES
    template_name = "products/student_order_history.html"
    context_object_name = "orders"

    def get_queryset(self):
        recipients = get_material_request_recipient_queryset(self.request.portal_person)
        return (
            RegistrationOrder.objects.filter(
                person__in=recipients,
                payment_status__in=(
                    PaymentStatus.PAID,
                    PaymentStatus.EXEMPTED,
                ),
            )
            .prefetch_related("items")
            .order_by("-paid_at", "-created_at")
        )


class AdminBackorderQueueView(AdministrativeRequiredMixin, ListView):
    template_name = "billing/admin_backorder_queue.html"
    context_object_name = "backorders"

    def get_queryset(self):
        return get_admin_backorder_queue()


def _build_product_groups(products):
    grouped = OrderedDict()
    for product in products:
        category = product.category
        key = category.pk
        if key not in grouped:
            total_products = sum(
                1 for p in products if p.category_id == category.pk
            )
            grouped[key] = {
                "category": category,
                "title": category.display_name,
                "badge": category.display_name,
                "product_count": total_products,
                "products": [],
            }
        grouped[key]["products"].append(product)
    return list(grouped.values())


def _resolve_purchase_person_or_message(request):
    actor = getattr(request, "portal_person", None)
    raw_person_id = request.POST.get("purchase_person_id")
    if actor is None and getattr(request, "portal_is_technical_admin", False):
        try:
            person_id = int(raw_person_id or 0)
        except (TypeError, ValueError):
            person_id = 0
        person = (
            Person.objects.filter(
                pk=person_id,
                is_active=True,
                person_type__is_active=True,
                person_type__code__in=MATERIAL_REQUEST_PERSON_TYPE_CODES,
            )
            .select_related("person_type")
            .first()
        )
    else:
        person = resolve_material_request_recipient(actor, raw_person_id)
    if person is None:
        messages.error(request, "Selecione uma pessoa válida para a solicitação.")
    return person


class ProductCategoryListView(AdministrativeRequiredMixin, ListView):
    model = ProductCategory
    template_name = "product_categories/product_category_list.html"
    context_object_name = "product_categories"

    def get_queryset(self):
        return ProductCategory.objects.annotate(
            product_count=Count("products", distinct=True)
        ).order_by("display_order", "display_name")


class ProductCategoryCreateView(ModalFormMixin, AdministrativeRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "product_categories/product_category_form.html"
    modal_name = "product-category-create"
    success_url = reverse_lazy("system:product-category-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Nova categoria"
        return context


class ProductCategoryUpdateView(ModalFormMixin, AdministrativeRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "product_categories/product_category_form.html"
    modal_name = "product-category-edit"
    success_url = reverse_lazy("system:product-category-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Editar categoria"
        return context


class ProductCategoryDeleteView(AdministrativeRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = "product_categories/product_category_confirm_delete.html"
    success_url = reverse_lazy("system:product-category-list")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f"Não foi possível excluir {self.object.display_name} porque há produtos vinculados.",
            )
            return redirect("system:product-category-list")


class ProductCategoryDetailView(AdministrativeRequiredMixin, DetailView):
    model = ProductCategory
    template_name = "product_categories/product_category_detail.html"
    context_object_name = "product_category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.object.products.order_by("display_name")
        return context
