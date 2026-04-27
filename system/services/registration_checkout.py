import json
import re
from decimal import Decimal

from django.db import transaction

from system.models.plan import SubscriptionPlan
from system.models.product import Product, ProductVariant
from system.models.registration_order import RegistrationOrder, RegistrationOrderItem
from system.services.financial_transactions import (
    apply_order_financials,
    resolve_payment_provider_for_plan,
)


ORDER_STOCK_APPLIED_MARKER = "[stock_applied]"
ORDER_ITEM_COLOR_PREFIX = "Cor: "
ORDER_ITEM_SIZE_PREFIX = "Tamanho: "

SIZE_SORT_ORDER = {
    "A0": 10,
    "A1": 11,
    "A2": 12,
    "A3": 13,
    "A4": 14,
    "A5": 15,
    "A6": 16,
    "F1": 21,
    "F2": 22,
    "F3": 23,
    "F4": 24,
    "M0": 31,
    "M1": 32,
    "M2": 33,
    "M3": 34,
    "M4": 35,
}

COLOR_SORT_ORDER = {
    "Branca": 10,
    "Branco": 10,
    "Cinza": 20,
    "Amarelo": 30,
    "Amarela": 30,
    "Laranja": 40,
    "Verde": 50,
    "Azul": 60,
    "Roxa": 70,
    "Marrom": 80,
    "Preto": 90,
}


def get_plan_catalog_payload():
    plans = SubscriptionPlan.objects.filter(is_active=True).exclude(
        requires_special_authorization=True
    )
    return [
        {
            "id": plan.pk,
            "code": plan.code,
            "name": plan.display_name,
            "price": str(plan.price),
            "monthly_reference_price": (
                str(plan.monthly_reference_price)
                if plan.monthly_reference_price is not None
                else ""
            ),
            "cycle": plan.get_billing_cycle_display(),
            "billing_cycle": plan.billing_cycle,
            "payment_method": plan.payment_method,
            "payment_method_label": plan.get_payment_method_display(),
            "is_family_plan": plan.is_family_plan,
            "audience": plan.audience,
            "audience_label": plan.get_audience_display(),
            "weekly_frequency": plan.weekly_frequency,
            "weekly_frequency_label": plan.get_weekly_frequency_display(),
            "teacher_commission_percentage": str(plan.teacher_commission_percentage),
            "requires_special_authorization": plan.requires_special_authorization,
            "installment_label": "1x" if plan.payment_method == "credit_card" else "",
        }
        for plan in plans
    ]


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
        payload.append(
            {
                "id": product.pk,
                "sku": product.sku,
                "name": product.display_name,
                "price": str(product.unit_price),
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
        "label": _build_variant_option_label(variant),
        "snapshot_name": build_order_item_product_name(product, variant),
        "color": variant.color,
        "size": variant.size,
        "stock_quantity": variant.stock_quantity,
        "is_in_stock": variant.stock_quantity > 0,
    }


def _build_variant_option_label(variant):
    parts = []
    if variant.color:
        parts.append(variant.color)
    if variant.size:
        parts.append(variant.size)
    if not parts:
        parts.append("Padrão")
    if variant.stock_quantity > 0:
        parts.append(f"{variant.stock_quantity} un.")
    else:
        parts.append("Esgotado")
    return " · ".join(parts)


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


def build_order_item_product_name(product, variant):
    details = []
    if variant.color:
        details.append(f"{ORDER_ITEM_COLOR_PREFIX}{variant.color}")
    if variant.size:
        details.append(f"{ORDER_ITEM_SIZE_PREFIX}{variant.size}")
    if not details:
        return product.display_name
    return f"{product.display_name} ({', '.join(details)})"


def normalize_selected_product_items(selected_products):
    if not selected_products:
        return []
    if selected_products and selected_products[0].get("variant") is not None:
        return selected_products
    return resolve_selected_product_items(selected_products)


@transaction.atomic
def create_product_only_order(person, cart_items):
    selections = normalize_selected_product_items(cart_items)
    if not selections:
        return None

    from system.models.registration_order import OrderKind

    order = RegistrationOrder.objects.create(
        person=person,
        plan=None,
        plan_price=Decimal("0"),
        total=Decimal("0"),
        kind=OrderKind.ONE_TIME,
    )

    items_total = Decimal("0")
    for selection in selections:
        subtotal = _create_product_order_item(order, selection)
        items_total += subtotal

    if items_total <= 0:
        order.delete()
        return None

    order.total = items_total
    order.save(update_fields=["total", "updated_at"])
    return order


def _create_product_order_item(order, selection):
    variant = selection["variant"]
    product = selection["product"]
    quantity = selection["quantity"]
    subtotal = product.unit_price * quantity
    RegistrationOrderItem.objects.create(
        order=order,
        product=product,
        product_name=build_order_item_product_name(product, variant),
        quantity=quantity,
        unit_price=product.unit_price,
        subtotal=subtotal,
    )
    return subtotal


def _count_group_members(cleaned_data):
    """
    Return number of participants for pricing calculations in family plans.
    Includes holder + dependent (if present) + any extra dependents.
    """
    count = 1
    if cleaned_data.get("dependent_name") or cleaned_data.get("dependent_cpf"):
        count += 1
    extras = cleaned_data.get("extra_dependents") or []
    if isinstance(extras, list):
        count += len(extras)
    return max(count, 1)


def get_registration_plan_multiplier(cleaned_data):
    return 1


@transaction.atomic
def create_registration_order(person, cleaned_data):
    plan_id = cleaned_data.get("selected_plan")
    selected_products = normalize_selected_product_items(
        cleaned_data.get("selected_products") or []
    )

    if not plan_id and not selected_products:
        return None

    plan = None
    plan_price = Decimal("0")
    if plan_id:
        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
            multiplier = 1
            if getattr(plan, "is_family_plan", False):
                multiplier = _count_group_members(cleaned_data)
            plan_price = plan.price * Decimal(multiplier)
        except SubscriptionPlan.DoesNotExist:
            pass

    order = RegistrationOrder.objects.create(
        person=person,
        plan=plan,
        plan_price=plan_price,
        total=Decimal("0"),
    )

    items_total = Decimal("0")
    for selection in selected_products:
        items_total += _create_product_order_item(order, selection)

    order.total = plan_price + items_total
    order.save(update_fields=["total", "updated_at"])
    apply_order_financials(
        order,
        payment_provider=resolve_payment_provider_for_plan(plan),
    )
    return order


@transaction.atomic
def apply_order_variant_stock(order):
    if order is None or _has_order_stock_applied(order):
        return order

    order_items = list(order.items.select_related("product"))
    if not order_items:
        return order

    deductions = []
    for item in order_items:
        variant = resolve_order_item_variant(item, lock=True)
        if variant is None:
            raise ValueError(f"Variante do pedido não encontrada para '{item.product_name}'.")
        if item.quantity > variant.stock_quantity:
            raise ValueError(
                f"Estoque insuficiente para {build_order_item_product_name(item.product, variant)}."
            )
        deductions.append((variant, item.quantity))

    for variant, quantity in deductions:
        variant.stock_quantity -= quantity
        variant.save(update_fields=["stock_quantity", "updated_at"])

    _mark_order_stock_applied(order)
    return order


def resolve_order_item_variant(order_item, *, lock=False):
    product = order_item.product
    if product is None:
        return None

    snapshot = _parse_order_item_variant_snapshot(order_item.product_name)
    queryset = ProductVariant.objects.filter(product=product, is_active=True)
    if lock:
        queryset = queryset.select_for_update()
    if snapshot["color"]:
        queryset = queryset.filter(color=snapshot["color"])
    if snapshot["size"]:
        queryset = queryset.filter(size=snapshot["size"])

    variants = list(queryset[:2])
    if len(variants) == 1:
        return variants[0]
    if not snapshot["color"] and not snapshot["size"] and len(variants) == 1:
        return variants[0]
    return None


def _parse_order_item_variant_snapshot(product_name):
    match = re.search(r"\((?P<details>[^()]*)\)$", product_name or "")
    if not match:
        return {"color": "", "size": ""}

    color = ""
    size = ""
    for raw_part in match.group("details").split(","):
        part = raw_part.strip()
        if part.startswith(ORDER_ITEM_COLOR_PREFIX):
            color = part[len(ORDER_ITEM_COLOR_PREFIX) :]
        elif part.startswith(ORDER_ITEM_SIZE_PREFIX):
            size = part[len(ORDER_ITEM_SIZE_PREFIX) :]
    return {"color": color, "size": size}


def _has_order_stock_applied(order):
    return ORDER_STOCK_APPLIED_MARKER in _get_order_note_lines(order)


def _mark_order_stock_applied(order):
    notes = _get_order_note_lines(order)
    if ORDER_STOCK_APPLIED_MARKER not in notes:
        notes.append(ORDER_STOCK_APPLIED_MARKER)
        order.notes = "\n".join(notes)
        order.save(update_fields=["notes", "updated_at"])


def _get_order_note_lines(order):
    return [line.strip() for line in (order.notes or "").splitlines() if line.strip()]
