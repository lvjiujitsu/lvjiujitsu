from django.db import transaction
from django.utils import timezone
from system.business_rule.models.membership import (
    MembershipCredit,
    MembershipCreditSource,
    MembershipStatus,
)
from system.business_rule.models.plan import PlanPrice
from system.business_rule.models.registration_order import OrderKind, RegistrationOrder
from system.business_rule.services.membership import add_billing_cycle
from system.business_rule.services.stripe_admin_actions import cancel_membership
from system.business_rule.services.membership_timeline import record_membership_event
from system.business_rule.services.family_pricing import recompute_family_discounts_for_person
from system.business_rule.models.membership_timeline import MembershipTimelineEventType
from system.business_rule.services.plan_change.calculation import calculate_plan_change
from system.business_rule.services.plan_change.primitives import current_plan_reference
from system.business_rule.services.plan_change.queries import get_last_paid_order_for_plan


def _assign_membership_plan(membership, new_plan):
    if isinstance(new_plan, PlanPrice):
        membership.plan = None
        membership.plan_price = new_plan
    else:
        membership.plan = new_plan
        membership.plan_price = None


@transaction.atomic
def create_plan_change_order(person, membership, new_plan, proration_data):
    additional = proration_data["additional_charge"]
    if additional <= 0:
        return None
    current_plan = proration_data["current_plan"]
    notes = (
        f"Upgrade de plano: {current_plan.display_name} → {new_plan.display_name}. "
        f"Saldo aplicado: R$ {proration_data['available_credit']}, "
        f"diferença a pagar: R$ {additional}."
    )
    is_new_plan_price = isinstance(new_plan, PlanPrice)
    order = RegistrationOrder.objects.create(
        person=person,
        plan=None if is_new_plan_price else new_plan,
        plan_price_ref=new_plan if is_new_plan_price else None,
        plan_price=additional,
        total=additional,
        kind=OrderKind.ONE_TIME,
        is_plan_change=True,
        notes=notes,
    )
    return order


def create_plan_change_stripe_order(person, membership, new_plan):
    current_plan = current_plan_reference(membership)
    is_new_plan_price = isinstance(new_plan, PlanPrice)
    notes = (
        "Migração de gateway: "
        f"{getattr(current_plan, 'display_name', '—')} → {new_plan.display_name} "
        "(assinatura Stripe recorrente)."
    )
    return RegistrationOrder.objects.create(
        person=person,
        plan=None if is_new_plan_price else new_plan,
        plan_price_ref=new_plan if is_new_plan_price else None,
        plan_price=new_plan.price,
        total=new_plan.price,
        kind=OrderKind.SUBSCRIPTION,
        is_plan_change=True,
        notes=notes,
    )


@transaction.atomic
def migrate_membership_off_stripe(membership):
    cancel_membership(
        membership,
        at_period_end=False,
        reason="Migração para plano fora do Stripe.",
    )
    membership.status = MembershipStatus.ACTIVE
    membership.stripe_subscription_id = ""
    membership.canceled_at = None
    membership.cancel_at_period_end = False
    membership.save(
        update_fields=[
            "status",
            "stripe_subscription_id",
            "canceled_at",
            "cancel_at_period_end",
            "updated_at",
        ]
    )
    return membership


@transaction.atomic
def apply_plan_change(order, membership, new_plan, *, proration=None):
    now = timezone.now()
    current_plan = current_plan_reference(membership)


    record_membership_event(
        membership.person,
        MembershipTimelineEventType.PLAN_CHANGED,
        membership=membership,
        actor=membership.person,
        context={
            "old_plan_name": current_plan.display_name if current_plan else "",
            "new_plan_name": new_plan.display_name,
            "old_price": str(current_plan.price) if current_plan else "",
            "new_price": str(new_plan.price),
        },
    )

    if order is not None and order.is_plan_change:
        _assign_membership_plan(membership, new_plan)
        membership.current_period_start = now
        membership.current_period_end = add_billing_cycle(now, new_plan.billing_cycle)
        membership.notes = (
            (membership.notes or "")
            + f"\nPlano alterado para {new_plan.display_name} em {now.strftime('%d/%m/%Y')} (upgrade pago)."
        ).strip()
        membership.save(
            update_fields=[
                "plan",
                "plan_price",
                "current_period_start",
                "current_period_end",
                "notes",
                "updated_at",
            ]
        )

        recompute_family_discounts_for_person(membership.person)
        return membership

    if proration is None:
        proration = calculate_plan_change(membership, new_plan)

    _assign_membership_plan(membership, new_plan)
    membership.current_period_start = now
    membership.current_period_end = proration["new_period_end"]
    membership.notes = (
        (membership.notes or "")
        + f"\nPlano alterado para {new_plan.display_name} em {now.strftime('%d/%m/%Y')}."
    ).strip()
    membership.save(
        update_fields=[
            "plan",
            "plan_price",
            "current_period_start",
            "current_period_end",
            "notes",
            "updated_at",
        ]
    )


    recompute_family_discounts_for_person(membership.person)

    leftover = proration["leftover_credit"]
    if leftover > 0:
        MembershipCredit.objects.create(
            membership=membership,
            amount=leftover,
            source=MembershipCreditSource.PLAN_CHANGE_LEFTOVER,
            source_order=get_last_paid_order_for_plan(
                membership.person, current_plan
            ),
            notes=(
                f"Sobra da troca: {current_plan.display_name} → {new_plan.display_name}. "
                f"{proration['cycles_covered']} ciclo(s) cobertos, "
                f"R$ {leftover} de sobra."
            ),
        )
    return membership
