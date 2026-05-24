import json
import re
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from system.constants import CheckoutAction
from system.models.plan import PlanPaymentMethod, SubscriptionPlan
from system.utils.plan_commercial import COMMERCIAL_TIER_LABELS, resolve_commercial_tier
from system.models.product import Product, ProductVariant
from system.models.registration_order import RegistrationOrder, RegistrationOrderItem, PaymentProvider
from system.services.financial_transactions import (
    apply_order_financials,
    calculate_gross_for_net,
    resolve_payment_provider_for_plan,
)
from system.services.pricing import catalog_unit_charges_for_display


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


_CYCLE_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}


def _build_installment_label(plan):
    if plan.payment_method != "credit_card":
        return ""
    n = _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan.monthly_reference_price:
        price_str = f"R$ {plan.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"


def _plan_charge_group_key(plan):
    tier = resolve_commercial_tier(
        code=plan.code, audience=plan.audience, is_family_plan=plan.is_family_plan
    )
    return (plan.audience, tier, plan.weekly_frequency, plan.is_family_plan, plan.billing_cycle)


def get_plan_catalog_payload():
    plans = list(
        SubscriptionPlan.objects.filter(is_active=True)
        .exclude(requires_special_authorization=True)
        .order_by("display_order", "price")
    )
    groups = {}
    for plan in plans:
        slot = groups.setdefault(_plan_charge_group_key(plan), {})
        slot[plan.payment_method] = plan
    cent = Decimal("0.01")
    payload = []
    for plan in plans:
        slot = groups[_plan_charge_group_key(plan)]
        pix_plan = slot.get(PlanPaymentMethod.PIX)
        card_plan = slot.get(PlanPaymentMethod.CREDIT_CARD)
        charge_pix = str(pix_plan.price.quantize(cent)) if pix_plan else "0.00"
        charge_card = str(card_plan.price.quantize(cent)) if card_plan else "0.00"
        tier = resolve_commercial_tier(
            code=plan.code, audience=plan.audience, is_family_plan=plan.is_family_plan
        )
        payload.append(
            {
                "id": plan.pk,
                "code": plan.code,
                "name": plan.display_name,
                "commercial_tier": tier,
                "commercial_tier_label": COMMERCIAL_TIER_LABELS.get(tier, tier),
                "price": str(plan.price),
                "charge_pix": charge_pix,
                "charge_card": charge_card,
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
                "is_loyalty_plan": plan.is_loyalty_plan,
                "audience": plan.audience,
                "audience_label": plan.get_audience_display(),
                "weekly_frequency": plan.weekly_frequency,
                "weekly_frequency_label": plan.get_weekly_frequency_display(),
                "teacher_commission_percentage": str(plan.teacher_commission_percentage),
                "requires_special_authorization": plan.requires_special_authorization,
                "installment_label": _build_installment_label(plan),
                "installment_count": (
                    _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
                    if plan.payment_method == "credit_card"
                    else 0
                ),
                "gateway_code": plan.gateway_code or "",
            }
        )
    return payload


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
    count = 1
    if cleaned_data.get("dependent_name") or cleaned_data.get("dependent_cpf"):
        count += 1
    extras = cleaned_data.get("extra_dependents") or []
    if isinstance(extras, list):
        count += len(extras)
    return max(count, 1)


def _count_training_persons(cleaned_data):
    from system.constants import RegistrationProfile
    profile = cleaned_data.get("registration_profile") or RegistrationProfile.HOLDER
    extras = cleaned_data.get("extra_dependents") or []
    extra_count = len(extras) if isinstance(extras, list) else 0
    if profile == RegistrationProfile.GUARDIAN:
        primary = 1 if (cleaned_data.get("student_name") or cleaned_data.get("student_cpf")) else 0
        return max(primary + extra_count, 1)
    # HOLDER: titular + dependente opcional
    deps = 1 if (cleaned_data.get("dependent_name") or cleaned_data.get("dependent_cpf")) else 0
    return max(1 + deps + extra_count, 1)


def get_registration_plan_multiplier(cleaned_data):
    return _count_training_persons(cleaned_data)


@transaction.atomic
def create_registration_order(person, cleaned_data):
    plan_id = cleaned_data.get("selected_plan")

    if not plan_id:
        return None

    plan = None
    plan_price = Decimal("0")
    try:
        plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
        if getattr(plan, "is_family_plan", False):
            multiplier = _count_group_members(cleaned_data)
        else:
            multiplier = _count_training_persons(cleaned_data)
        plan_price = plan.price * Decimal(multiplier)
    except SubscriptionPlan.DoesNotExist:
        return None

    payment_provider = resolve_payment_provider_for_plan(plan)
    total = plan_price

    order = RegistrationOrder.objects.create(
        person=person,
        plan=plan,
        plan_price=plan_price,
        total=total,
    )
    apply_order_financials(order, payment_provider=payment_provider)
    return order


def _apply_fee_pass_through(base_amount, payment_provider):
    if payment_provider == PaymentProvider.ASAAS and getattr(settings, "PIX_FEE_PASS_THROUGH", True):
        return calculate_gross_for_net(base_amount, payment_provider)
    return base_amount


def gross_up_order_for_checkout(order, checkout_action):
    """Aplica gross-up de taxa ao total do pedido de acordo com o método de pagamento escolhido."""
    payment_method = None
    if checkout_action == CheckoutAction.ASAAS_CARD:
        if not getattr(settings, "CREDIT_CARD_FEE_PASS_THROUGH", True):
            return order
        provider = PaymentProvider.ASAAS
        payment_method = PlanPaymentMethod.CREDIT_CARD
    elif checkout_action == CheckoutAction.PIX:
        if not getattr(settings, "PIX_FEE_PASS_THROUGH", True):
            return order
        provider = PaymentProvider.ASAAS
        payment_method = PlanPaymentMethod.PIX
    else:
        return order
    gross = calculate_gross_for_net(
        order.total or Decimal("0"),
        provider,
        payment_method=payment_method,
    )
    if gross != order.total:
        order.total = gross
        order.save(update_fields=["total", "updated_at"])
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
