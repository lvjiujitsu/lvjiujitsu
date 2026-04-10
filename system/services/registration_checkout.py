import json
from decimal import Decimal

from django.db import transaction

from system.models.plan import SubscriptionPlan
from system.models.product import Product
from system.models.registration_order import RegistrationOrder, RegistrationOrderItem


def get_plan_catalog_payload():
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return [
        {
            "id": plan.pk,
            "name": plan.display_name,
            "price": str(plan.price),
            "cycle": plan.get_billing_cycle_display(),
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
            plan_price = plan.price
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
    return order
