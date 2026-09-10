import json
from system.business_rule.models.product import Product, ProductVariant
from system.business_rule.services.order_stock import build_order_item_product_name
from system.business_rule.services.pricing import catalog_unit_charges_for_display
from system.business_rule.services.registration_checkout.labels import COLOR_SORT_ORDER, SIZE_SORT_ORDER, build_variant_option_label


def get_product_catalog_payload():
    products = (
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        .select_related("category")
        .prefetch_related("variants")
    )
    payload = []
    for product in products:
        variants = [
            _build_product_variant_payload(product, variant)
            for variant in _get_active_variants(product)
        ]
        charges = catalog_unit_charges_for_display(product.unit_price)
        payload.append(
            {
                "id": product.pk,
                "sku": product.sku,
                "name": product.display_name,
                "price": str(product.unit_price),
                "charge_pix": charges["charge_pix"],
                "charge_card": charges["charge_card"],
                "category": str(product.category),
                "category_code": product.category.code,
                "category_order": product.category.display_order,
                "description": product.description or "",
                "variant_count": len(variants),
                "total_stock": sum(variant["stock_quantity"] for variant in variants),
                "variants": variants,
            }
        )
    return payload


def _build_product_variant_payload(product, variant):
    return {
        "id": variant.pk,
        "product_id": product.pk,
        "product_name": product.display_name,
        "label": build_variant_option_label(variant),
        "snapshot_name": build_order_item_product_name(product, variant),
        "color": variant.color,
        "size": variant.size,
        "stock_quantity": variant.stock_quantity,
        "is_in_stock": variant.stock_quantity > 0,
    }


def _get_active_variants(product):
    variants = [variant for variant in product.variants.all() if variant.is_active]
    return sorted(
        variants,
        key=lambda variant: (
            COLOR_SORT_ORDER.get(variant.color, 999),
            variant.color or "",
            SIZE_SORT_ORDER.get(variant.size, 999),
            variant.size or "",
            variant.pk,
        ),
    )


def parse_selected_products(raw_payload):
    if not raw_payload:
        return []
    try:
        items = json.loads(raw_payload)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            variant_id = int(item.get("variant_id") or item.get("id") or 0)
            quantity = int(item.get("qty") or item.get("quantity") or 0)
        except (ValueError, TypeError):
            continue
        if variant_id > 0 and 0 < quantity <= 99:
            result.append({"variant_id": variant_id, "quantity": quantity})
    return result


def resolve_selected_product_items(raw_items):
    if not raw_items:
        return []

    quantities_by_variant = {}
    ordered_variant_ids = []
    for item in raw_items:
        variant_id = int(item.get("variant_id") or 0)
        quantity = int(item.get("quantity") or 0)
        if variant_id <= 0 or quantity <= 0:
            continue
        if variant_id not in quantities_by_variant:
            ordered_variant_ids.append(variant_id)
            quantities_by_variant[variant_id] = 0
        quantities_by_variant[variant_id] += quantity

    if not ordered_variant_ids:
        return []

    variants_by_id = {
        variant.pk: variant
        for variant in ProductVariant.objects.select_related("product", "product__category")
        .filter(
            pk__in=ordered_variant_ids,
            is_active=True,
            product__is_active=True,
            product__category__is_active=True,
        )
    }

    selections = []
    for variant_id in ordered_variant_ids:
        variant = variants_by_id.get(variant_id)
        if variant is None:
            raise ValueError("Selecione apenas materiais válidos.")
        quantity = quantities_by_variant[variant_id]
        if quantity > variant.stock_quantity:
            raise ValueError(
                f"Estoque insuficiente para {build_order_item_product_name(variant.product, variant)}."
            )
        selections.append(
            {
                "variant_id": variant.pk,
                "variant": variant,
                "product": variant.product,
                "quantity": quantity,
            }
        )
    return selections


def normalize_selected_product_items(selected_products):
    if not selected_products:
        return []
    if selected_products and selected_products[0].get("variant") is not None:
        return selected_products
    return resolve_selected_product_items(selected_products)
