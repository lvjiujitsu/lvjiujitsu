from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from system.constants import CheckoutAction
from system.models.plan import PlanPaymentMethod
from system.models.registration_order import DepositStatus, PaymentProvider
from system.runtime_config import decimal_setting


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def resolve_plan_from_order(order):
    if order is None:
        return None
    if order.plan_id is not None:
        return order.plan
    plan_price_ref = getattr(order, "plan_price_ref", None)
    if plan_price_ref is not None:
        return plan_price_ref
    if getattr(order, "plan_price_ref_id", None):
        return order.plan_price_ref
    return None


def resolve_payment_provider_for_plan(plan):
    if plan is None:
        return PaymentProvider.NONE
    gateway_code = getattr(plan, "gateway_code", "") or ""
    if gateway_code.startswith("stripe"):
        return PaymentProvider.STRIPE
    payment_method = getattr(plan, "payment_method", None)
    if payment_method == PlanPaymentMethod.PIX:
        return PaymentProvider.ASAAS
    if payment_method == PlanPaymentMethod.CREDIT_CARD:
        return PaymentProvider.ASAAS
    return PaymentProvider.NONE


def resolve_checkout_action_for_plan(plan):
    if plan is None:
        return CheckoutAction.PAY_LATER
    if plan.payment_method == PlanPaymentMethod.PIX:
        return CheckoutAction.PIX
    if plan.payment_method == PlanPaymentMethod.CREDIT_CARD:
        if getattr(plan, "gateway_code", "") == "stripe_card":
            return CheckoutAction.STRIPE_CARD
        return CheckoutAction.ASAAS_CARD
    return CheckoutAction.PAY_LATER


def calculate_gross_for_net(net_amount, payment_provider, *, payment_method=None):
    net = _money(net_amount)
    if net <= ZERO:
        return net
    if payment_provider == PaymentProvider.ASAAS and payment_method == PlanPaymentMethod.CREDIT_CARD:
        percent = decimal_setting("ASAAS_CREDIT_PERCENT_FEE")
        fixed = decimal_setting("ASAAS_CREDIT_FIXED_FEE")
        return _money((net + fixed) / (Decimal("1") - percent))
    if payment_provider == PaymentProvider.ASAAS:
        return _money(net + decimal_setting("ASAAS_PIX_FIXED_FEE"))
    if payment_provider == PaymentProvider.STRIPE:
        percent = decimal_setting("STRIPE_CREDIT_PERCENT_FEE")
        fixed = decimal_setting("STRIPE_CREDIT_FIXED_FEE")
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
    resolved_plan = resolve_plan_from_order(order)
    if provider is None:
        provider = order.payment_provider or resolve_payment_provider_for_plan(resolved_plan)

    amounts = calculate_financial_amounts(order.total or ZERO, provider, plan=resolved_plan)
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
        return _money(min(decimal_setting("ASAAS_PIX_FIXED_FEE"), gross))
    if payment_provider == PaymentProvider.STRIPE:
        return _money(
            (gross * decimal_setting("STRIPE_CREDIT_PERCENT_FEE"))
            + decimal_setting("STRIPE_CREDIT_FIXED_FEE")
        )
    return ZERO


def _money(value):
    return Decimal(value or ZERO).quantize(CENT, rounding=ROUND_HALF_UP)
