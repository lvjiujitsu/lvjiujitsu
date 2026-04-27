from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.models.product_backorder import (
    ProductBackorder,
    ProductBackorderStatus,
)
from system.models.registration_order import OrderKind, RegistrationOrder, RegistrationOrderItem
from system.selectors.product_backorders import (
    get_active_backorder,
    get_expired_ready_backorders,
    get_pending_queue_for_variant,
)
from system.services.registration_checkout import build_order_item_product_name


class ProductBackorderError(Exception):
    pass


def _reservation_duration():
    days = getattr(settings, "BACKORDER_RESERVATION_DAYS", 7)
    return timedelta(days=days)


@transaction.atomic
def create_backorder(person, variant, *, notes=""):
    if person is None or variant is None:
        raise ProductBackorderError("Pessoa e variante são obrigatórios.")
    if not variant.is_active or not variant.product.is_active:
        raise ProductBackorderError("Produto não está disponível.")

    existing = get_active_backorder(person, variant)
    if existing is not None:
        return existing

    return ProductBackorder.objects.create(
        person=person,
        variant=variant,
        status=ProductBackorderStatus.PENDING,
        notes=notes or "",
    )


@transaction.atomic
def restock_variant(variant, quantity_added):
    if quantity_added <= 0:
        return []

    locked_variant = (
        type(variant).objects.select_for_update().get(pk=variant.pk)
    )
    pending_qs = get_pending_queue_for_variant(locked_variant).select_for_update()
    pending = list(pending_qs[:quantity_added])

    if not pending:
        return []

    now = timezone.now()
    expires_at = now + _reservation_duration()

    promoted = []
    for backorder in pending:
        backorder.status = ProductBackorderStatus.READY
        backorder.notified_at = now
        backorder.expires_at = expires_at
        backorder.save(
            update_fields=("status", "notified_at", "expires_at", "updated_at")
        )
        promoted.append(backorder)

    return promoted


@transaction.atomic
def confirm_backorder(backorder):
    if backorder.status != ProductBackorderStatus.READY:
        raise ProductBackorderError("Apenas reservas prontas podem ser confirmadas.")

    variant = backorder.variant
    product = variant.product

    order = RegistrationOrder.objects.create(
        person=backorder.person,
        plan=None,
        plan_price=Decimal("0"),
        total=product.unit_price,
        kind=OrderKind.ONE_TIME,
    )
    RegistrationOrderItem.objects.create(
        order=order,
        product=product,
        product_name=build_order_item_product_name(product, variant),
        quantity=1,
        unit_price=product.unit_price,
        subtotal=product.unit_price,
    )

    backorder.status = ProductBackorderStatus.CONFIRMED
    backorder.confirmed_at = timezone.now()
    backorder.confirmed_order = order
    backorder.save(
        update_fields=("status", "confirmed_at", "confirmed_order", "updated_at")
    )
    return order


@transaction.atomic
def cancel_backorder(backorder):
    if backorder.status not in (
        ProductBackorderStatus.PENDING,
        ProductBackorderStatus.READY,
    ):
        raise ProductBackorderError("Apenas reservas ativas podem ser canceladas.")

    was_ready = backorder.status == ProductBackorderStatus.READY
    backorder.status = ProductBackorderStatus.CANCELED
    backorder.canceled_at = timezone.now()
    backorder.save(update_fields=("status", "canceled_at", "updated_at"))

    if was_ready:
        restock_variant(backorder.variant, 1)

    return backorder


@transaction.atomic
def expire_pending_reservations(reference_time=None):
    now = reference_time or timezone.now()
    expired_qs = get_expired_ready_backorders(now).select_for_update()
    expired = list(expired_qs)
    if not expired:
        return []

    promotions_per_variant = {}
    for backorder in expired:
        backorder.status = ProductBackorderStatus.EXPIRED
        backorder.save(update_fields=("status", "updated_at"))
        variant_id = backorder.variant_id
        promotions_per_variant[variant_id] = promotions_per_variant.get(variant_id, 0) + 1

    promoted_total = []
    for variant_id, freed in promotions_per_variant.items():
        variant = expired[0].variant if expired[0].variant_id == variant_id else None
        if variant is None:
            from system.models.product import ProductVariant
            variant = ProductVariant.objects.get(pk=variant_id)
        promoted_total.extend(restock_variant(variant, freed))

    return {
        "expired": expired,
        "promoted": promoted_total,
    }


@transaction.atomic
def cancel_all_active_for_variant(variant, *, reason=""):
    affected = ProductBackorder.objects.filter(
        variant=variant,
        status__in=(ProductBackorderStatus.PENDING, ProductBackorderStatus.READY),
    ).select_for_update()
    canceled = []
    now = timezone.now()
    for backorder in affected:
        backorder.status = ProductBackorderStatus.CANCELED
        backorder.canceled_at = now
        if reason:
            backorder.notes = (backorder.notes + "\n" + reason).strip()
        backorder.save(update_fields=("status", "canceled_at", "notes", "updated_at"))
        canceled.append(backorder)
    return canceled
