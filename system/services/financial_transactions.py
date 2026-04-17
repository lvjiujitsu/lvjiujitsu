from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from system.models.plan import PlanPaymentMethod
from system.models.registration_order import DepositStatus, PaymentProvider


ASAAS_PIX_FIXED_FEE = Decimal("1.99")
STRIPE_CREDIT_PERCENT_FEE = Decimal("0.0399")
STRIPE_CREDIT_FIXED_FEE = Decimal("0.39")
ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def resolve_payment_provider_for_plan(plan):
    if plan is None:
        return PaymentProvider.NONE
    if plan.payment_method == PlanPaymentMethod.PIX:
        return PaymentProvider.ASAAS
    if plan.payment_method == PlanPaymentMethod.CREDIT_CARD:
        return PaymentProvider.STRIPE
    return PaymentProvider.NONE


def resolve_checkout_action_for_plan(plan):
    provider = resolve_payment_provider_for_plan(plan)
    if provider == PaymentProvider.ASAAS:
        return "pix"
    if provider == PaymentProvider.STRIPE:
        return "stripe"
    return "pay_later"


def calculate_financial_amounts(gross_amount, payment_provider):
    gross = _money(gross_amount)
    fee = _calculate_fee(gross, payment_provider)
    return {
        "gross_amount": gross,
        "administrative_fee": fee,
        "net_amount": _money(max(gross - fee, ZERO)),
    }


@transaction.atomic
def apply_order_financials(
    order,
    *,
    payment_provider=None,
    financial_transaction_id="",
    mark_available=False,
    expected_deposit_date=None,
):
    provider = payment_provider
    if provider is None:
        provider = order.payment_provider or resolve_payment_provider_for_plan(order.plan)

    amounts = calculate_financial_amounts(order.total or ZERO, provider)
    order.payment_provider = provider
    if financial_transaction_id:
        order.financial_transaction_id = financial_transaction_id
    order.administrative_fee = amounts["administrative_fee"]
    order.net_amount = amounts["net_amount"]
    if expected_deposit_date is not None:
        order.expected_deposit_date = expected_deposit_date
    elif mark_available and not order.expected_deposit_date:
        order.expected_deposit_date = timezone.localdate()
    if mark_available:
        order.deposit_status = DepositStatus.AVAILABLE
    elif not order.deposit_status:
        order.deposit_status = DepositStatus.PENDING
    order.save(
        update_fields=[
            "payment_provider",
            "financial_transaction_id",
            "administrative_fee",
            "net_amount",
            "deposit_status",
            "expected_deposit_date",
            "updated_at",
        ]
    )
    return order


def _calculate_fee(gross, payment_provider):
    if gross <= ZERO:
        return ZERO
    if payment_provider == PaymentProvider.ASAAS:
        return _money(min(ASAAS_PIX_FIXED_FEE, gross))
    if payment_provider == PaymentProvider.STRIPE:
        return _money((gross * STRIPE_CREDIT_PERCENT_FEE) + STRIPE_CREDIT_FIXED_FEE)
    return ZERO


def _money(value):
    return Decimal(value or ZERO).quantize(CENT, rounding=ROUND_HALF_UP)
