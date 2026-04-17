from django.db import transaction
from django.utils import timezone

from system.models.trial_access import TrialAccessGrant
from system.services.membership import get_latest_open_order


def get_active_trial_for_person(person):
    return (
        TrialAccessGrant.objects.filter(person=person, is_active=True)
        .order_by("-created_at")
        .first()
    )


def has_active_trial_for_person(person):
    grant = get_active_trial_for_person(person)
    return bool(grant and grant.remaining_classes > 0)


@transaction.atomic
def grant_trial_for_order(order, *, classes=1, notes=""):
    if classes < 1:
        raise ValueError("Quantidade de aulas experimentais deve ser maior que zero.")

    grant, created = TrialAccessGrant.objects.get_or_create(
        order=order,
        defaults={
            "person": order.person,
            "granted_classes": classes,
            "consumed_classes": 0,
            "is_active": True,
            "activated_at": timezone.now(),
            "notes": notes or "",
        },
    )
    if not created:
        grant.person = order.person
        grant.granted_classes = max(grant.granted_classes, classes)
        grant.is_active = grant.remaining_classes > 0
        if notes:
            grant.notes = notes
        grant.save(
            update_fields=(
                "person",
                "granted_classes",
                "is_active",
                "notes",
                "updated_at",
            )
        )
    return grant


@transaction.atomic
def consume_trial_for_person(person, *, only_if_payment_pending=True):
    if only_if_payment_pending and get_latest_open_order(person) is None:
        return None

    grant = get_active_trial_for_person(person)
    if grant is None or not grant.can_consume:
        return None

    grant.consumed_classes += 1
    if grant.remaining_classes <= 0:
        grant.is_active = False
        grant.consumed_at = timezone.now()
    grant.save(
        update_fields=(
            "consumed_classes",
            "is_active",
            "consumed_at",
            "updated_at",
        )
    )
    return grant
