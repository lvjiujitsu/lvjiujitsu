from django import forms
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory

from system.models.product import Product, ProductCategory, ProductVariant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "sku",
            "display_name",
            "category",
            "unit_price",
            "description",
            "is_active",
        )
        labels = {
            "sku": "SKU",
            "display_name": "Nome do produto",
            "category": "Categoria",
            "unit_price": "Preço unitário (R$)",
            "description": "Descrição",
            "is_active": "Produto ativo",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "unit_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_cat_id = getattr(self.instance, "category_id", None)
        self.fields["category"].queryset = (
            ProductCategory.objects.filter(
                Q(is_active=True) | Q(pk=current_cat_id),
            )
            .distinct()
            .order_by("display_order", "display_name")
        )
        self.fields["category"].empty_label = "Selecione"


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ("size", "color", "stock_quantity", "is_active")
        labels = {
            "size": "Tamanho",
            "color": "Cor",
            "stock_quantity": "Estoque",
            "is_active": "Ativo",
        }
        widgets = {
            "stock_quantity": forms.NumberInput(attrs={"min": "0"}),
        }


class BaseProductVariantFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            size = form.cleaned_data.get("size", "")
            color = form.cleaned_data.get("color", "")
            if not size and not color:
                continue
            key = (size.strip().lower(), color.strip().lower())
            if key in seen:
                form.add_error("color", "Variante duplicada (mesma cor e tamanho).")
            seen.add(key)


def get_product_variant_formset(*, data=None, instance=None):
    target = instance or Product()
    formset_class = inlineformset_factory(
        Product,
        ProductVariant,
        form=ProductVariantForm,
        formset=BaseProductVariantFormSet,
        extra=1,
        can_delete=True,
    )
    return formset_class(data=data, instance=target, prefix="variants")
