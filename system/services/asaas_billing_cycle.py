import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from system.models.membership import Membership, MembershipStatus
from system.models.registration_order import PaymentProvider, PaymentStatus, RegistrationOrder
from system.services.asaas_checkout import (
    create_credit_card_charge_for_order,
    create_pix_charge_for_order,
)

logger = logging.getLogger(__name__)

ASAAS_GATEWAY_CODES = ("asaas_pix", "asaas_card")


def _has_pending_renewal_order(membership):
    lookup = {"person_id": membership.person_id, "payment_status": PaymentStatus.PENDING}
    if membership.plan_price_id:
        lookup["plan_price_ref_id"] = membership.plan_price_id
    else:
        lookup["plan_id"] = membership.plan_id
    return RegistrationOrder.objects.filter(**lookup).exists()


def find_due_asaas_memberships(*, lead_days=3, reference=None):
    reference = reference or timezone.now()
    window_end = reference + timedelta(days=lead_days)

    candidates = (
        Membership.objects.filter(
            status=MembershipStatus.ACTIVE,
            current_period_end__isnull=False,
            current_period_end__gte=reference,
            current_period_end__lte=window_end,
        )
        .exclude(plan_price__isnull=True, plan__isnull=True)
        .select_related("plan_price__tier", "plan", "person")
    )

    due = []
    for membership in candidates:
        if membership.effective_gateway_code not in ASAAS_GATEWAY_CODES:
            continue
        if _has_pending_renewal_order(membership):
            continue
        due.append(membership)
    return due


@transaction.atomic
def generate_due_asaas_charge(membership):
    if membership.family_discount_applied and membership.billed_price is not None:
        amount = membership.billed_price
    else:
        amount = membership.effective_full_price

    order = RegistrationOrder.objects.create(
        person=membership.person,
        plan=membership.plan,
        plan_price_ref=membership.plan_price,
        plan_price=amount,
        total=amount,
        payment_status=PaymentStatus.PENDING,
        payment_provider=PaymentProvider.ASAAS,
        notes="Cobrança de renovação gerada automaticamente.",
    )

    if membership.effective_gateway_code == "asaas_card":
        create_credit_card_charge_for_order(order)
    else:
        create_pix_charge_for_order(order)

    return order


def generate_due_asaas_charges(*, lead_days=3, reference=None):
    generated = []
    skipped = []
    for membership in find_due_asaas_memberships(lead_days=lead_days, reference=reference):
        try:
            order = generate_due_asaas_charge(membership)
            generated.append(order)
        except Exception:
            logger.exception(
                "generate_due_asaas_charges: falha ao gerar cobrança (membership=%s).",
                membership.pk,
            )
            skipped.append(membership)
    return {"generated": generated, "skipped": skipped}
