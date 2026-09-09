from decimal import Decimal

from django.conf import settings

from system.business_rule.models.plan import PlanPaymentMethod
from system.business_rule.models.registration_order import PaymentProvider
from system.business_rule.services.financial_transactions import calculate_gross_for_net


def catalog_unit_charges_for_display(unit_price) -> dict[str, str]:
    net = Decimal(str(unit_price or "0")).quantize(Decimal("0.01"))
    cent = Decimal("0.01")
    if net <= 0:
        return {"charge_pix": "0.00", "charge_card": "0.00"}
    pix = net
    if getattr(settings, "PIX_FEE_PASS_THROUGH", True):
        pix = calculate_gross_for_net(net, PaymentProvider.ASAAS)
    card = net
    if getattr(settings, "CREDIT_CARD_FEE_PASS_THROUGH", True):
        card = calculate_gross_for_net(
            net,
            PaymentProvider.ASAAS,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
        )
    return {
        "charge_pix": str(pix.quantize(cent)),
        "charge_card": str(card.quantize(cent)),
    }
