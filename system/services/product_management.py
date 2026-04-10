from django.db import transaction
from django.db.models import Count, Q, Sum

from system.models.product import Product


@transaction.atomic
def save_product_with_variants(*, form, variant_formset):
    product = form.save()
    variant_formset.instance = product
    variant_formset.save()
    return product


def get_product_list_cards():
    return (
        Product.objects.select_related("category")
        .annotate(
            _variant_count=Count("variants", filter=Q(variants__is_active=True)),
            _total_stock=Sum(
                "variants__stock_quantity",
                filter=Q(variants__is_active=True),
            ),
        )
        .order_by("category__display_order", "display_name")
    )


def get_public_product_cards():
    return (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related("variants")
        .annotate(
            _total_stock=Sum(
                "variants__stock_quantity",
                filter=Q(variants__is_active=True),
            ),
        )
        .order_by("category__display_order", "display_name")
    )


def get_product_card_by_pk(pk):
    return (
        Product.objects.select_related("category")
        .prefetch_related("variants")
        .get(pk=pk)
    )
