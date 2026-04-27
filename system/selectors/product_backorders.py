from django.db.models import Q

from system.models.product_backorder import (
    ACTIVE_BACKORDER_STATUSES,
    ProductBackorder,
    ProductBackorderStatus,
)


def get_active_backorder(person, variant):
    return (
        ProductBackorder.objects.filter(
            person=person,
            variant=variant,
            status__in=ACTIVE_BACKORDER_STATUSES,
        )
        .order_by("-created_at")
        .first()
    )


def get_backorders_for_person(person):
    return (
        ProductBackorder.objects.filter(person=person)
        .select_related("variant", "variant__product", "confirmed_order")
        .order_by(
            "-status",
            "-created_at",
        )
    )


def get_ready_backorders_for_person(person):
    return (
        ProductBackorder.objects.filter(
            person=person,
            status=ProductBackorderStatus.READY,
        )
        .select_related("variant", "variant__product")
        .order_by("expires_at", "created_at")
    )


def count_ready_backorders_for_person(person):
    if person is None:
        return 0
    return ProductBackorder.objects.filter(
        person=person,
        status=ProductBackorderStatus.READY,
    ).count()


def get_pending_queue_for_variant(variant):
    return (
        ProductBackorder.objects.filter(
            variant=variant,
            status=ProductBackorderStatus.PENDING,
        )
        .select_related("person")
        .order_by("created_at")
    )


def get_admin_backorder_queue():
    return (
        ProductBackorder.objects.filter(status__in=ACTIVE_BACKORDER_STATUSES)
        .select_related("person", "variant", "variant__product")
        .order_by("variant__product__display_name", "variant__color", "variant__size", "created_at")
    )


def get_expired_ready_backorders(reference_time):
    return ProductBackorder.objects.filter(
        status=ProductBackorderStatus.READY,
        expires_at__lt=reference_time,
    )


def has_active_backorder_for_variant(person, variant):
    return ProductBackorder.objects.filter(
        person=person,
        variant=variant,
        status__in=ACTIVE_BACKORDER_STATUSES,
    ).exists()
