from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from django.utils.formats import date_format

from system.models.membership import (
    MembershipCredit,
    MembershipCreditSource,
    MembershipCreditStatus,
    MembershipStatus,
)
from system.models.plan import PlanPrice
from system.models.registration_order import (
    OrderKind,
    PaymentProvider,
    PaymentStatus,
    RegistrationOrder,
)
from system.selectors.plan_eligibility import (
    build_eligibility_context_for_person,
    get_eligible_plan_prices,
    get_eligible_plans,
)
from system.services.membership import (
    MONTHS_BY_BILLING_CYCLE,
    _add_months,
    add_billing_cycle,
    get_membership_owner,
)
from system.services.asaas_client import AsaasClientError, refund_payment
from system.services.payroll_rules import append_order_refund_record
from system.services.registration_checkout import (
    CATALOG_ID_PREFIX_PLAN_PRICE,
    CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
    build_catalog_plan_id,
)
from system.services.stripe_admin_actions import (
    StripeAdminActionError,
    cancel_membership,
    refund_order,
)
from system.utils.plan_commercial import COMMERCIAL_TIER_LABELS, resolve_commercial_tier


def _catalog_id_for_plan(plan_obj):
    if isinstance(plan_obj, PlanPrice):
        return build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, plan_obj.pk)
    return build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, plan_obj.pk)


def _current_plan_reference(membership):
    if membership.plan_price_id is not None:
        return membership.plan_price
    return membership.plan


class PlanChangeError(Exception):
    pass


_CYCLE_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}

_STRIPE_RECURRING_GATEWAY_CODE = "stripe_card"
_PLAN_CHANGE_LOCKED_STATUSES = (
    MembershipStatus.ACTIVE,
    MembershipStatus.EXEMPTED,
)


def _quantize(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def plan_requires_stripe_checkout(plan):
    return getattr(plan, "gateway_code", "") == _STRIPE_RECURRING_GATEWAY_CODE


def is_plan_change_locked(membership):
    if (
        membership is None
        or membership.status not in _PLAN_CHANGE_LOCKED_STATUSES
        or (membership.plan_id is None and membership.plan_price_id is None)
    ):
        return False
    if membership.plan_price_id is not None:
        gateway_code = membership.plan_price.gateway_code
    else:
        gateway_code = getattr(membership.plan, "gateway_code", "")
    is_stripe_recurring = bool(
        membership.stripe_subscription_id
        or gateway_code == _STRIPE_RECURRING_GATEWAY_CODE
    )
    if not is_stripe_recurring:
        return False
    if membership.current_period_end is None:
        return True
    return membership.current_period_end > timezone.now()


def get_plan_change_lock(membership):
    if not is_plan_change_locked(membership):
        return {
            "is_locked": False,
            "available_on": None,
            "message": "",
        }

    available_on = _membership_period_end_date(membership)
    if available_on:
        message = (
            "Troca e cancelamento liberados em "
            f"{date_format(available_on, 'SHORT_DATE_FORMAT')}, "
            "após a carência da assinatura recorrente."
        )
    else:
        message = (
            "Troca e cancelamento bloqueados durante a carência da assinatura recorrente. "
            "Fale com a academia para consultar a data de liberação."
        )
    return {
        "is_locked": True,
        "available_on": available_on,
        "message": message,
    }


def _membership_period_end_date(membership):
    period_end = getattr(membership, "current_period_end", None)
    if period_end is None:
        return None
    if timezone.is_aware(period_end):
        return timezone.localtime(period_end).date()
    return period_end.date()


def get_last_paid_order(membership):
    queryset = RegistrationOrder.objects.filter(
        person=membership.person,
        payment_status__in=(PaymentStatus.PAID, PaymentStatus.EXEMPTED),
        total__gt=Decimal("0"),
    ).filter(refunded_at__isnull=True)
    if membership.plan_price_id is not None:
        queryset = queryset.filter(plan_price_ref=membership.plan_price)
    else:
        queryset = queryset.filter(plan=membership.plan)
    return queryset.order_by("-paid_at", "-created_at").first()


def get_membership_amount_paid(membership):
    last_order = get_last_paid_order(membership)
    if last_order is not None and last_order.total:
        return _quantize(last_order.total)
    full_price = membership.effective_full_price
    if full_price:
        return _quantize(full_price)
    return Decimal("0.00")


def _build_installment_label(plan):
    if plan.payment_method != "credit_card":
        return ""
    n = _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
    if n <= 1:
        return "1x"
    if plan.monthly_reference_price:
        price_str = f"R$ {plan.monthly_reference_price:.2f}".replace(".", ",")
        return f"{n}x {price_str}"
    return f"{n}x"


def serialize_plan_with_proration(plan, proration, *, is_current=False):
    is_plan_price = isinstance(plan, PlanPrice)
    is_family_plan = False if is_plan_price else plan.is_family_plan
    is_loyalty_plan = False if is_plan_price else plan.is_loyalty_plan
    tier = resolve_commercial_tier(
        is_family_plan=is_family_plan, is_loyalty_plan=is_loyalty_plan
    )
    code = (
        f"{plan.tier.code}-{plan.gateway_code}-{plan.billing_cycle}"
        if is_plan_price
        else plan.code
    )
    return {
        "id": _catalog_id_for_plan(plan),
        "code": code,
        "name": plan.display_name,
        "commercial_tier": tier,
        "commercial_tier_label": COMMERCIAL_TIER_LABELS.get(tier, tier),
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
        "is_family_plan": is_family_plan,
        "audience": plan.audience,
        "audience_label": (
            plan.tier.get_audience_display() if is_plan_price else plan.get_audience_display()
        ),
        "weekly_frequency": plan.weekly_frequency,
        "weekly_frequency_label": (
            plan.tier.get_weekly_frequency_display()
            if is_plan_price
            else plan.get_weekly_frequency_display()
        ),
        "installment_label": _build_installment_label(plan),
        "installment_count": (
            _CYCLE_INSTALLMENTS.get(plan.billing_cycle, 1)
            if plan.payment_method == "credit_card"
            else 0
        ),
        "gateway_code": plan.gateway_code,
        "requires_checkout": plan.gateway_code == _STRIPE_RECURRING_GATEWAY_CODE,
        "is_current": is_current,
        "proration": (
            {
                "cycles_covered": proration["cycles_covered"],
                "extension_months": proration["extension_months"],
                "new_period_end": proration["new_period_end"].isoformat(),
                "leftover_credit": str(proration["leftover_credit"]),
                "additional_charge": str(proration["additional_charge"]),
                "is_upgrade": proration["is_upgrade"],
                "is_extension": proration["is_extension"],
                "has_leftover": proration["has_leftover"],
            }
            if proration is not None
            else {
                "cycles_covered": 0,
                "extension_months": 0,
                "new_period_end": "",
                "leftover_credit": "0.00",
                "additional_charge": "0.00",
                "is_upgrade": False,
                "is_extension": False,
                "has_leftover": False,
            }
        ),
    }


def build_membership_summary(membership):
    if membership is None:
        return None
    last_order = get_last_paid_order(membership)
    amount_paid = (
        Decimal(last_order.total) if last_order and last_order.total
        else Decimal(membership.effective_full_price or 0)
    )
    period_start = membership.current_period_start
    period_end = membership.current_period_end
    cycle_days = max((period_end - period_start).days, 1) if period_start and period_end else 0
    now = timezone.now()
    days_used = max(0, min((now - period_start).days, cycle_days)) if period_start else 0
    days_remaining = max(0, cycle_days - days_used)

    if amount_paid > 0 and cycle_days > 0:
        daily = amount_paid / Decimal(cycle_days)
        consumed = (daily * Decimal(days_used)).quantize(Decimal("0.01"))
        available = (amount_paid - consumed).quantize(Decimal("0.01"))
    else:
        consumed = Decimal("0.00")
        available = Decimal("0.00")
    if available < 0:
        available = Decimal("0.00")

    return {
        "plan_name": membership.effective_display_name,
        "plan_cycle": membership.effective_billing_cycle_display,
        "amount_paid": str(amount_paid.quantize(Decimal("0.01"))),
        "amount_consumed": str(consumed),
        "available_credit": str(available),
        "cycle_days": cycle_days,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "period_end": period_end.isoformat() if period_end else "",
        "payment_provider": last_order.payment_provider if last_order else "",
        "refund_supported": bool(
            last_order
            and last_order.payment_provider in ("stripe", "asaas")
            and (last_order.stripe_payment_intent_id or last_order.asaas_payment_id)
        ),
    }


def build_plan_catalog(person, membership):
    if not membership or membership.status not in (
        MembershipStatus.ACTIVE,
        MembershipStatus.EXEMPTED,
    ):
        return []
    if is_plan_change_locked(membership):
        return []
    billing_owner = get_membership_owner(person) or person
    eligibility = build_eligibility_context_for_person(billing_owner)
    current_plan = _current_plan_reference(membership)
    current_catalog_id = _catalog_id_for_plan(current_plan) if current_plan is not None else None

    legacy_plans = (
        get_eligible_plans(eligibility)
        .filter(is_loyalty_plan=True)
        .exclude(pk=membership.plan_id)
    )
    plan_prices = get_eligible_plan_prices(eligibility).exclude(pk=membership.plan_price_id)

    catalog = []
    if current_plan is not None:
        catalog.append(serialize_plan_with_proration(current_plan, None, is_current=True))
    for plan in list(legacy_plans) + list(plan_prices):
        if _catalog_id_for_plan(plan) == current_catalog_id:
            continue
        try:
            proration = calculate_plan_change(membership, plan)
        except PlanChangeError:
            continue
        catalog.append(serialize_plan_with_proration(plan, proration))
    return catalog


def build_plan_catalog_filters(catalog):
    frequencies = []
    seen_frequencies = set()
    cycles = []
    seen_cycles = set()
    methods = []
    seen_methods = set()
    for plan in catalog:
        freq = plan["weekly_frequency"]
        if freq not in seen_frequencies:
            seen_frequencies.add(freq)
            frequencies.append({"value": freq, "label": plan["weekly_frequency_label"]})
        cycle = plan["billing_cycle"]
        if cycle not in seen_cycles:
            seen_cycles.add(cycle)
            cycles.append({"value": cycle, "label": plan["cycle"]})
        method = plan["payment_method"]
        if method not in seen_methods:
            seen_methods.add(method)
            methods.append({"value": method, "label": plan["payment_method_label"]})
    frequencies.sort(key=lambda item: item["value"])
    return {
        "frequencies": frequencies,
        "cycles": cycles,
        "methods": methods,
    }


def calculate_plan_change(membership, new_plan):
    if membership.status not in (MembershipStatus.ACTIVE, MembershipStatus.EXEMPTED):
        raise PlanChangeError("Somente assinaturas ativas podem trocar de plano.")
    if not membership.current_period_start or not membership.current_period_end:
        raise PlanChangeError("Assinatura sem período definido.")
    current_plan = _current_plan_reference(membership)
    if current_plan is not None and _catalog_id_for_plan(current_plan) == _catalog_id_for_plan(new_plan):
        raise PlanChangeError("Plano selecionado é o mesmo que o atual.")

    now = timezone.now()
    period_start = membership.current_period_start
    period_end = membership.current_period_end

    cycle_days = (period_end - period_start).days
    if cycle_days <= 0:
        raise PlanChangeError("Ciclo de cobrança inválido.")

    days_used = max(0, min((now - period_start).days, cycle_days))
    days_remaining = cycle_days - days_used

    amount_paid = get_membership_amount_paid(membership)

    if amount_paid <= 0:
        amount_consumed = Decimal("0.00")
        available_credit = Decimal("0.00")
    else:
        daily_value = (amount_paid / Decimal(cycle_days)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        amount_consumed = _quantize(daily_value * Decimal(days_used))
        available_credit = _quantize(amount_paid - amount_consumed)
        if available_credit < 0:
            available_credit = Decimal("0.00")

    new_price = _quantize(new_plan.price or Decimal("0"))

    if new_price <= 0:
        cycles_covered = 1
        leftover_credit = available_credit
        additional_charge = Decimal("0.00")
    elif available_credit >= new_price:
        cycles_covered = int(available_credit // new_price)
        leftover_credit = _quantize(
            available_credit - (Decimal(cycles_covered) * new_price)
        )
        additional_charge = Decimal("0.00")
    else:
        cycles_covered = 1
        leftover_credit = Decimal("0.00")
        additional_charge = _quantize(new_price - available_credit)

    extension_months = cycles_covered * MONTHS_BY_BILLING_CYCLE.get(
        new_plan.billing_cycle, 1
    )
    new_period_end = _add_months(now, extension_months)

    is_upgrade = additional_charge > 0
    is_extension = not is_upgrade and cycles_covered >= 1
    has_leftover = leftover_credit > 0

    return {
        "current_plan": current_plan,
        "new_plan": new_plan,
        "cycle_days": cycle_days,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "amount_paid": amount_paid,
        "amount_consumed": amount_consumed,
        "available_credit": available_credit,
        "cycles_covered": cycles_covered,
        "extension_months": extension_months,
        "new_period_end": new_period_end,
        "leftover_credit": leftover_credit,
        "additional_charge": additional_charge,
        "is_upgrade": is_upgrade,
        "is_extension": is_extension,
        "has_leftover": has_leftover,
        "period_end": period_end,
        "now": now,
    }


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
    current_plan = _current_plan_reference(membership)
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
    current_plan = _current_plan_reference(membership)

    from system.services.membership_timeline import record_membership_event
    from system.models.membership_timeline import MembershipTimelineEventType

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
        from system.services.family_pricing import recompute_family_discounts_for_person

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

    from system.services.family_pricing import recompute_family_discounts_for_person

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


def get_last_paid_order_for_plan(person, plan):
    lookup = (
        {"plan_price_ref": plan} if isinstance(plan, PlanPrice) else {"plan": plan}
    )
    return (
        RegistrationOrder.objects.filter(
            person=person,
            payment_status__in=(PaymentStatus.PAID, PaymentStatus.EXEMPTED),
            total__gt=Decimal("0"),
            **lookup,
        )
        .order_by("-paid_at", "-created_at")
        .first()
    )


@transaction.atomic
def refund_plan_change_leftover(membership, amount, *, source_order=None, current_plan=None):
    plan_for_lookup = current_plan or _current_plan_reference(membership)
    last_order = source_order or get_last_paid_order_for_plan(
        membership.person, plan_for_lookup
    )
    if last_order is None:
        raise PlanChangeError(
            "Nenhuma cobrança paga encontrada para devolver o valor."
        )

    provider = last_order.payment_provider
    refund_reference = ""

    if provider == PaymentProvider.STRIPE:
        if not last_order.stripe_payment_intent_id:
            raise PlanChangeError(
                "Pedido Stripe sem PaymentIntent — não é possível estornar."
            )
        try:
            result = refund_order(
                last_order,
                amount=amount,
                reason="Sobra de troca de plano",
            )
        except StripeAdminActionError as exc:
            raise PlanChangeError(f"Falha no estorno Stripe: {exc}") from exc
        refund_reference = str(result.get("refund_id") or "")
    elif provider == PaymentProvider.ASAAS:
        if not last_order.asaas_payment_id:
            raise PlanChangeError(
                "Pedido Asaas sem ID de pagamento — não é possível estornar."
            )
        try:
            result = refund_payment(
                last_order.asaas_payment_id,
                value=amount,
                description="Sobra de troca de plano",
            )
        except AsaasClientError as exc:
            raise PlanChangeError(f"Falha no estorno Asaas: {exc}") from exc
        refund_reference = str(result.get("id") or "")
        last_order.refunded_at = timezone.now()
        append_order_refund_record(
            last_order,
            amount,
            source="asaas_plan_change_refund",
            cumulative=True,
            reason="Sobra de troca de plano",
            save=False,
        )
        last_order.save(
            update_fields=["refunded_at", "notes", "updated_at"]
        )
    else:
        raise PlanChangeError(
            "Pagamento original não suporta devolução automática."
        )

    credit = MembershipCredit.objects.create(
        membership=membership,
        amount=amount,
        source=MembershipCreditSource.PLAN_CHANGE_LEFTOVER,
        status=MembershipCreditStatus.REFUNDED,
        source_order=last_order,
        refund_provider=provider or "",
        refund_provider_reference=refund_reference,
        refunded_at=timezone.now(),
        notes="Sobra de troca de plano devolvida ao cliente.",
    )
    return credit


@transaction.atomic
def apply_plan_change_with_leftover_refund(
    membership, new_plan, proration, *, source_order=None
):
    current_plan = membership.plan
    membership = apply_plan_change(
        None, membership, new_plan, proration=proration
    )
    leftover = proration["leftover_credit"]
    if leftover <= 0:
        return membership, None

    available_credit = (
        MembershipCredit.objects.filter(
            membership=membership,
            status=MembershipCreditStatus.AVAILABLE,
            source=MembershipCreditSource.PLAN_CHANGE_LEFTOVER,
        )
        .order_by("-created_at")
        .first()
    )

    refund = refund_plan_change_leftover(
        membership,
        leftover,
        source_order=source_order,
        current_plan=current_plan,
    )

    if available_credit is not None:
        available_credit.status = MembershipCreditStatus.REFUNDED
        available_credit.refund_provider = refund.refund_provider
        available_credit.refund_provider_reference = refund.refund_provider_reference
        available_credit.refunded_at = refund.refunded_at
        available_credit.notes = (
            (available_credit.notes or "")
            + " | Convertido em devolução automática."
        ).strip()
        available_credit.save(
            update_fields=[
                "status",
                "refund_provider",
                "refund_provider_reference",
                "refunded_at",
                "notes",
                "updated_at",
            ]
        )
        refund.delete()
        return membership, available_credit
    return membership, refund
