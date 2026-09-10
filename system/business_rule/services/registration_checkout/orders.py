from decimal import Decimal
from django.conf import settings
from django.db import transaction
from system.business_rule.constants import CheckoutAction
from system.business_rule.models.plan import PlanPaymentMethod
from system.business_rule.models.registration_order import RegistrationOrder, RegistrationOrderItem, PaymentProvider
from system.business_rule.services.financial_transactions import (
    apply_order_financials,
    calculate_gross_for_net,
    resolve_payment_provider_for_plan,
)
from system.business_rule.services.order_stock import build_order_item_product_name
from system.business_rule.models.registration_order import OrderKind
from system.business_rule.constants import RegistrationProfile
from system.business_rule.services.registration_checkout.catalog_ids import resolve_catalog_plan
from system.business_rule.services.registration_checkout.product_catalog import normalize_selected_product_items


@transaction.atomic
def create_product_only_order(person, cart_items):
    selections = normalize_selected_product_items(cart_items)
    if not selections:
        return None


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
    profile = cleaned_data.get("registration_profile") or RegistrationProfile.HOLDER
    extras = cleaned_data.get("extra_dependents") or []
    extra_count = len(extras) if isinstance(extras, list) else 0
    if profile == RegistrationProfile.GUARDIAN:
        primary = 1 if (cleaned_data.get("student_name") or cleaned_data.get("student_cpf")) else 0
        return max(primary + extra_count, 1)
    deps = 1 if (cleaned_data.get("dependent_name") or cleaned_data.get("dependent_cpf")) else 0
    return max(1 + deps + extra_count, 1)


def get_registration_plan_multiplier(cleaned_data):
    return _count_training_persons(cleaned_data)


@transaction.atomic
def create_registration_order(person, cleaned_data):
    catalog_id = cleaned_data.get("selected_plan")

    if not catalog_id:
        return None

    legacy_plan, plan_price_ref = resolve_catalog_plan(catalog_id)
    if legacy_plan is None and plan_price_ref is None:
        return None

    if legacy_plan is not None:
        resolved_plan = legacy_plan
        if getattr(legacy_plan, "is_family_plan", False):
            multiplier = _count_group_members(cleaned_data)
        else:
            multiplier = _count_training_persons(cleaned_data)
        unit_price = legacy_plan.price
    else:
        resolved_plan = plan_price_ref
        multiplier = _count_training_persons(cleaned_data)
        unit_price = plan_price_ref.price

    total = unit_price * Decimal(multiplier)
    payment_provider = resolve_payment_provider_for_plan(resolved_plan)

    order = RegistrationOrder.objects.create(
        person=person,
        plan=legacy_plan,
        plan_price_ref=plan_price_ref,
        plan_price=total,
        total=total,
    )
    apply_order_financials(order, payment_provider=payment_provider)
    return order


def _apply_fee_pass_through(base_amount, payment_provider):
    if payment_provider == PaymentProvider.ASAAS and getattr(settings, "PIX_FEE_PASS_THROUGH", True):
        return calculate_gross_for_net(base_amount, payment_provider)
    return base_amount


def gross_up_order_for_checkout(order, checkout_action):
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
