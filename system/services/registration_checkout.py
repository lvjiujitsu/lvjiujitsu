import json
from decimal import Decimal

from django.db import transaction

from system.constants import RegistrationProfile
from system.models.category import CategoryAudience
from system.models.plan import SubscriptionPlan
from system.models.product import Product
from system.models.registration_order import RegistrationOrder, RegistrationOrderItem
from system.services.financial_transactions import (
    apply_order_financials,
    resolve_payment_provider_for_plan,
)


def get_plan_catalog_payload():
    plans = SubscriptionPlan.objects.filter(is_active=True)
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
            "installment_label": "1x" if plan.payment_method == "credit_card" else "",
        }
        for plan in plans
    ]


def get_product_catalog_payload():
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related("category")
    return [
        {
            "id": product.pk,
            "name": product.display_name,
            "price": str(product.unit_price),
            "category": str(product.category),
        }
        for product in products
    ]


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
            product_id = int(item.get("id", 0))
            quantity = int(item.get("qty", 0))
        except (ValueError, TypeError):
            continue
        if product_id > 0 and quantity > 0:
            result.append({"id": product_id, "qty": quantity})
    return result


@transaction.atomic
def create_product_only_order(person, cart_items):
    if not cart_items:
        return None

    product_ids = [item["product_id"] for item in cart_items]
    products_by_id = {
        p.pk: p for p in Product.objects.filter(pk__in=product_ids, is_active=True)
    }

    from system.models.registration_order import OrderKind

    order = RegistrationOrder.objects.create(
        person=person,
        plan=None,
        plan_price=Decimal("0"),
        total=Decimal("0"),
        kind=OrderKind.ONE_TIME,
    )

    items_total = Decimal("0")
    for item in cart_items:
        product = products_by_id.get(item["product_id"])
        if not product:
            continue
        qty = item["quantity"]
        subtotal = product.unit_price * qty
        RegistrationOrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.display_name,
            quantity=qty,
            unit_price=product.unit_price,
            subtotal=subtotal,
        )
        items_total += subtotal

    if items_total <= 0:
        order.delete()
        return None

    order.total = items_total
    order.save(update_fields=["total", "updated_at"])
    return order


def get_registration_plan_multiplier(cleaned_data):
    child_group_sets = []
    profile = cleaned_data.get("registration_profile")
    if profile == RegistrationProfile.GUARDIAN:
        child_group_sets.append(cleaned_data.get("student_class_groups") or [])
    if profile == RegistrationProfile.HOLDER and cleaned_data.get("include_dependent"):
        child_group_sets.append(cleaned_data.get("dependent_class_groups") or [])
    for dependent in cleaned_data.get("extra_dependents") or []:
        child_group_sets.append(dependent.get("class_groups") or [])

    for class_groups in child_group_sets:
        audiences = {
            class_group.class_category.audience
            for class_group in class_groups
            if class_group is not None and class_group.class_category_id
        }
        if {CategoryAudience.KIDS, CategoryAudience.JUVENILE}.issubset(audiences):
            return 2
    return 1


@transaction.atomic
def create_registration_order(person, cleaned_data):
    plan_id = cleaned_data.get("selected_plan")
    products_payload = parse_selected_products(
        cleaned_data.get("selected_products_payload")
    )

    if not plan_id and not products_payload:
        return None

    plan = None
    plan_price = Decimal("0")
    if plan_id:
        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
            plan_price = plan.price * Decimal(get_registration_plan_multiplier(cleaned_data))
        except SubscriptionPlan.DoesNotExist:
            pass

    order = RegistrationOrder.objects.create(
        person=person,
        plan=plan,
        plan_price=plan_price,
        total=Decimal("0"),
    )

    items_total = Decimal("0")
    if products_payload:
        product_ids = [item["id"] for item in products_payload]
        products_by_id = {
            p.pk: p
            for p in Product.objects.filter(pk__in=product_ids, is_active=True)
        }
        for item in products_payload:
            product = products_by_id.get(item["id"])
            if not product:
                continue
            qty = item["qty"]
            subtotal = product.unit_price * qty
            RegistrationOrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.display_name,
                quantity=qty,
                unit_price=product.unit_price,
                subtotal=subtotal,
            )
            items_total += subtotal

    order.total = plan_price + items_total
    order.save(update_fields=["total", "updated_at"])
    apply_order_financials(
        order,
        payment_provider=resolve_payment_provider_for_plan(plan),
    )
    return order
