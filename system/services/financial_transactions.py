from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.constants import CheckoutAction
from system.models.plan import PlanPaymentMethod
from system.models.registration_order import DepositStatus, PaymentProvider


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def resolve_payment_provider_for_plan(plan):
    if plan is None:
        return PaymentProvider.NONE
    if plan.payment_method == PlanPaymentMethod.PIX:
        return PaymentProvider.ASAAS
    if plan.payment_method == PlanPaymentMethod.CREDIT_CARD:
        return PaymentProvider.ASAAS
    return PaymentProvider.NONE


def resolve_checkout_action_for_plan(plan):
    if plan is None:
        return CheckoutAction.PAY_LATER
    if plan.payment_method == PlanPaymentMethod.PIX:
        return CheckoutAction.PIX
    if plan.payment_method == PlanPaymentMethod.CREDIT_CARD:
        return CheckoutAction.ASAAS_CARD
    return CheckoutAction.PAY_LATER


def calculate_gross_for_net(net_amount, payment_provider, *, payment_method=None):
    """Retorna o valor bruto a cobrar do cliente para que a academia receba net_amount líquido."""
    net = _money(net_amount)
    if net <= ZERO:
        return net
    if payment_provider == PaymentProvider.ASAAS and payment_method == PlanPaymentMethod.CREDIT_CARD:
        percent = _decimal_setting("ASAAS_CREDIT_PERCENT_FEE")
        fixed = _decimal_setting("ASAAS_CREDIT_FIXED_FEE")
        return _money((net + fixed) / (Decimal("1") - percent))
    if payment_provider == PaymentProvider.ASAAS:
        return _money(net + _decimal_setting("ASAAS_PIX_FIXED_FEE"))
    if payment_provider == PaymentProvider.STRIPE:
        percent = _decimal_setting("STRIPE_CREDIT_PERCENT_FEE")
        fixed = _decimal_setting("STRIPE_CREDIT_FIXED_FEE")
        return _money((net + fixed) / (Decimal("1") - percent))
    return net


def calculate_financial_amounts(gross_amount, payment_provider, *, plan=None):
    gross = _money(gross_amount)
    fee = _calculate_fee(gross, payment_provider, plan=plan)
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

    amounts = calculate_financial_amounts(order.total or ZERO, provider, plan=order.plan)
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


def _calculate_fee(gross, payment_provider, *, plan=None):
    if gross <= ZERO:
        return ZERO
    if plan is not None and getattr(plan, "gateway_code", "").startswith("asaas_"):
        fixed = Decimal(str(plan.gateway_fixed_fee or ZERO))
        percent = Decimal(str(plan.gateway_percentage_fee or ZERO))
        return _money(min((gross * percent) + fixed, gross))
    if payment_provider == PaymentProvider.ASAAS:
        return _money(min(_decimal_setting("ASAAS_PIX_FIXED_FEE"), gross))
    if payment_provider == PaymentProvider.STRIPE:
        return _money(
            (gross * _decimal_setting("STRIPE_CREDIT_PERCENT_FEE"))
            + _decimal_setting("STRIPE_CREDIT_FIXED_FEE")
        )
    return ZERO


def _money(value):
    return Decimal(value or ZERO).quantize(CENT, rounding=ROUND_HALF_UP)


def _decimal_setting(name):
    return Decimal(str(getattr(settings, name)))
