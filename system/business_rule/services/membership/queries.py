from decimal import Decimal
from django.db.models import Q
from system.business_rule.models.membership import Membership, MembershipStatus
from system.business_rule.models.person import PersonRelationship, PersonRelationshipKind
from system.business_rule.models.registration_order import PaymentStatus, RegistrationOrder
from system.business_rule.services.membership.activation import activate_membership_from_paid_order


def get_active_memberships_for_people(people):
    person_ids = [person.pk for person in people if person is not None]
    if not person_ids:
        return {}
    memberships = (
        Membership.objects.filter(person_id__in=person_ids)
        .exclude(status__in=(MembershipStatus.EXPIRED, MembershipStatus.CANCELED))
        .select_related("plan_price__tier", "plan")
        .prefetch_related("pause_requests")
        .order_by("person_id", "-created_at")
    )
    active_by_person = {}
    for membership in memberships:
        active_by_person.setdefault(membership.person_id, membership)
    return active_by_person


def get_active_membership(person, billing_owner=None, *, memberships_by_person=None):
    billing_person = billing_owner if billing_owner is not None else get_membership_owner(person)
    if memberships_by_person is not None:
        cached = memberships_by_person.get(billing_person.pk)
        if cached is not None:
            return cached
    return _ensure_active_membership_for_person(billing_person)


def get_membership_owner(person):
    if person is None:
        return None
    if _person_has_financial_records(person):
        return person
    for responsible in _get_responsible_people(person):
        if _person_has_financial_records(responsible):
            return responsible
    return person


def _get_responsible_people(person):
    relationships = (
        PersonRelationship.objects.filter(
            target_person=person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            source_person__is_active=True,
        )
        .select_related("source_person")
        .order_by("-created_at")
    )
    return [item.source_person for item in relationships]


def _person_has_financial_records(person):
    return Membership.objects.filter(person=person).exists() or RegistrationOrder.objects.filter(
        person=person
    ).exists()


def _ensure_active_membership_for_person(person):
    if person is None:
        return None
    active_membership = (
        Membership.objects.filter(person=person)
        .exclude(status__in=(MembershipStatus.EXPIRED, MembershipStatus.CANCELED))
        .select_related("plan_price__tier", "plan")
        .prefetch_related("pause_requests")
        .order_by("-created_at")
        .first()
    )
    if active_membership is not None:
        return active_membership
    latest_paid_order = (
        RegistrationOrder.objects.filter(
            person=person,
            payment_status__in=(PaymentStatus.PAID, PaymentStatus.EXEMPTED),
        )
        .filter(
            Q(plan__isnull=False) | Q(plan_price_ref__isnull=False)
        )
        .exclude(total__lte=Decimal("0"))
        .select_related("plan", "plan_price_ref")
        .order_by("-paid_at", "-created_at")
        .first()
    )
    if latest_paid_order is None:
        return None
    return activate_membership_from_paid_order(
        latest_paid_order,
        notes="Assinatura sincronizada a partir de pedido já pago.",
    )


def has_dependents(person):
    return PersonRelationship.objects.filter(
        source_person=person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    ).exists()


def get_latest_open_order(person):
    billing_person = get_membership_owner(person)
    if billing_person is None:
        return None
    return (
        RegistrationOrder.objects.filter(person=billing_person, total__gt=0)
        .exclude(
            payment_status__in=(
                PaymentStatus.PAID,
                PaymentStatus.EXEMPTED,
                PaymentStatus.REFUNDED,
            )
        )
        .order_by("-created_at")
        .first()
    )
