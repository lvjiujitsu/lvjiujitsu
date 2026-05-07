from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.db import models

from system.models.asaas import PayoutStatus, TeacherPayout
from system.models.registration_order import (
    DepositStatus,
    PaymentProvider,
    PaymentStatus,
    RegistrationOrder,
)
from system.services import asaas_client


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def build_financial_dashboard():
    asaas = _build_asaas_snapshot()
    stripe_snapshot = _build_stripe_snapshot()
    local = _build_local_totals()
    history = _build_financial_history()
    return {
        "asaas": asaas,
        "stripe": stripe_snapshot,
        "local": local,
        "totals": {
            "available": _money(asaas["available"] + stripe_snapshot["available"]),
            "receivable": _money(asaas["receivable"] + stripe_snapshot["receivable"]),
            "local_receivable": _money(
                local["asaas_local_receivable"] + local["stripe_local_receivable"]
            ),
            "gross_inflows": local["gross_inflows"],
            "net_inflows": local["net_inflows"],
            "outflows": local["outflows"],
            "balance_after_outflows": _money(
                local["net_inflows"] - local["outflows"]
            ),
        },
        "history": history,
    }


def _build_asaas_snapshot():
    if not settings.ASAAS_API_KEY or not settings.ASAAS_API_URL:
        return _unavailable_provider("ASAAS", "ASAAS não configurado.")
    try:
        balance = asaas_client.get_balance()
        stats = asaas_client.get_payment_statistics(status="PENDING")
    except asaas_client.AsaasClientError as exc:
        return _unavailable_provider("ASAAS", str(exc))
    return {
        "name": "ASAAS",
        "available": _money(balance.get("balance")),
        "receivable": _money(stats.get("netValue") or stats.get("value")),
        "gross_receivable": _money(stats.get("value")),
        "quantity": int(stats.get("quantity") or 0),
        "status": "available",
        "error": "",
    }


def _build_stripe_snapshot():
    if not settings.STRIPE_SECRET_KEY:
        return _unavailable_provider("Stripe", "Stripe não configurado.")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        balance = stripe.Balance.retrieve()
    except Exception as exc:
        return _unavailable_provider("Stripe", str(exc))
    return {
        "name": "Stripe",
        "available": _stripe_amount(balance, "available"),
        "receivable": _stripe_amount(balance, "pending"),
        "gross_receivable": _stripe_amount(balance, "pending"),
        "quantity": 0,
        "status": "available",
        "error": "",
    }


def _build_local_totals():
    orders = RegistrationOrder.objects.filter(total__gt=0)
    inflow_statuses = (PaymentStatus.PAID, PaymentStatus.EXEMPTED)
    inflows = orders.filter(payment_status__in=inflow_statuses)
    pending = orders.exclude(payment_status__in=inflow_statuses + (PaymentStatus.REFUNDED,))
    outflow_statuses = (
        PayoutStatus.PENDING,
        PayoutStatus.APPROVED,
        PayoutStatus.SENT,
        PayoutStatus.PAID,
    )
    outflows = TeacherPayout.objects.filter(status__in=outflow_statuses)
    return {
        "gross_inflows": _aggregate_money(inflows, "total"),
        "net_inflows": _aggregate_net_inflows(inflows),
        "pending_orders": _aggregate_money(pending, "total"),
        "asaas_local_receivable": _aggregate_money(
            orders.filter(
                payment_provider=PaymentProvider.ASAAS,
                deposit_status__in=(DepositStatus.PENDING, DepositStatus.AVAILABLE),
            ),
            "net_amount",
        ),
        "stripe_local_receivable": _aggregate_money(
            orders.filter(
                payment_provider=PaymentProvider.STRIPE,
                deposit_status__in=(DepositStatus.PENDING, DepositStatus.AVAILABLE),
            ),
            "net_amount",
        ),
        "outflows": _aggregate_money(outflows, "amount"),
    }


def _build_financial_history(limit=40):
    entries = []
    orders = (
        RegistrationOrder.objects.filter(total__gt=0)
        .select_related("person", "plan")
        .order_by("-created_at")[:limit]
    )
    for order in orders:
        amount = _money(order.net_amount if order.net_amount else order.total)
        entries.append(
            {
                "direction": "inflow",
                "kind": "Entrada",
                "person": order.person,
                "description": order.plan.display_name if order.plan_id else f"Pedido #{order.pk}",
                "provider": order.get_payment_provider_display() or "Não definido",
                "status": order.get_payment_status_display(),
                "amount": amount,
                "date": order.paid_at or order.created_at,
                "expected_date": order.expected_deposit_date,
                "reference": order.financial_transaction_id
                or order.stripe_payment_intent_id
                or order.asaas_payment_id
                or f"pedido-{order.pk}",
                "summary": order.notes,
            }
        )

    payouts = (
        TeacherPayout.objects.select_related("person")
        .order_by("-created_at")[:limit]
    )
    for payout in payouts:
        entries.append(
            {
                "direction": "outflow",
                "kind": "Saída",
                "person": payout.person,
                "description": payout.get_kind_display(),
                "provider": "ASAAS PIX",
                "status": payout.get_status_display(),
                "amount": _money(payout.amount),
                "date": payout.paid_at or payout.sent_at or payout.created_at,
                "expected_date": payout.scheduled_for,
                "reference": payout.asaas_transfer_id or f"repasse-{payout.pk}",
                "summary": payout.approval_notes,
            }
        )
    entries.sort(key=lambda entry: entry["date"], reverse=True)
    return entries[:limit]


def _unavailable_provider(name, error):
    return {
        "name": name,
        "available": ZERO,
        "receivable": ZERO,
        "gross_receivable": ZERO,
        "quantity": 0,
        "status": "unavailable",
        "error": error,
    }


def _stripe_amount(balance, key):
    rows = balance.get(key) if isinstance(balance, dict) else getattr(balance, key, [])
    total = ZERO
    for row in rows or []:
        currency = row.get("currency") if isinstance(row, dict) else getattr(row, "currency", "")
        if str(currency).lower() != settings.PAYMENT_CURRENCY:
            continue
        amount = row.get("amount") if isinstance(row, dict) else getattr(row, "amount", 0)
        total += _money(Decimal(amount or 0) / Decimal("100"))
    return _money(total)


def _aggregate_money(queryset, field_name):
    result = queryset.aggregate(total=models.Sum(field_name))
    return _money(result["total"])


def _aggregate_net_inflows(queryset):
    total = ZERO
    for order in queryset:
        total += _money(order.net_amount if order.net_amount else order.total)
    return _money(total)


def _money(value):
    if value in (None, ""):
        return ZERO
    try:
        return Decimal(str(value).replace(",", ".")).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return ZERO
