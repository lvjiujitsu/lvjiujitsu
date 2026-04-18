from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from system.models.membership import Membership, MembershipStatus
from system.models.plan import SubscriptionPlan
from system.models.registration_order import OrderKind, RegistrationOrder
from system.services.membership import _cycle_duration


class PlanChangeError(Exception):
    pass


def calculate_plan_change(membership, new_plan):
    if membership.status not in (MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED):
        raise PlanChangeError("Somente assinaturas ativas podem trocar de plano.")
    if not membership.current_period_start or not membership.current_period_end:
        raise PlanChangeError("Assinatura sem período definido.")
    if membership.plan_id == new_plan.pk:
        raise PlanChangeError("Plano selecionado é o mesmo que o atual.")

    now = timezone.now()
    period_start = membership.current_period_start
    period_end = membership.current_period_end

    cycle_days = (period_end - period_start).days
    if cycle_days <= 0:
        raise PlanChangeError("Ciclo de cobrança inválido.")

    days_used = max(0, min((now - period_start).days, cycle_days))
    days_remaining = cycle_days - days_used

    current_plan = membership.plan
    current_daily_rate = (current_plan.price / Decimal(cycle_days)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    new_cycle_days = _cycle_duration(new_plan.billing_cycle).days
    new_daily_rate = (new_plan.price / Decimal(new_cycle_days)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    credit = (current_daily_rate * Decimal(days_remaining)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    cost = (new_daily_rate * Decimal(days_remaining)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    net = (cost - credit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "current_plan": current_plan,
        "new_plan": new_plan,
        "cycle_days": cycle_days,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "current_daily_rate": current_daily_rate,
        "new_daily_rate": new_daily_rate,
        "credit_unused_days": credit,
        "cost_remaining_days": cost,
        "net_amount": net,
        "is_upgrade": net > 0,
        "is_downgrade": net < 0,
        "is_free_switch": net == 0,
        "period_end": period_end,
    }


@transaction.atomic
def create_plan_change_order(person, membership, new_plan, proration_data):
    net = proration_data["net_amount"]
    if net <= 0:
        return None

    current_plan = proration_data["current_plan"]
    order = RegistrationOrder.objects.create(
        person=person,
        plan=new_plan,
        plan_price=net,
        total=net,
        kind=OrderKind.ONE_TIME,
        is_plan_change=True,
        notes=(
            f"Troca de plano: {current_plan.display_name} \u2192 {new_plan.display_name}. "
            f"Cr\u00e9dito: R$ {proration_data['credit_unused_days']}, "
            f"Custo: R$ {proration_data['cost_remaining_days']}."
        ),
    )
    return order


@transaction.atomic
def apply_plan_change(order, membership, new_plan):
    membership.plan = new_plan
    membership.notes = (
        membership.notes
        + f"\nPlano alterado para {new_plan.display_name} em {timezone.now().strftime('%d/%m/%Y')}."
    ).strip()
    membership.save(update_fields=["plan", "notes", "updated_at"])
    return membership
