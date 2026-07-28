import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from system.models.person import Person
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.services import asaas_client
from system.services.financial_transactions import apply_order_financials
from system.models.registration_order import PaymentProvider
from system.runtime_config import site_name


logger = logging.getLogger(__name__)


class AsaasCheckoutError(Exception):
    pass


def ensure_asaas_customer(person):
    if person.asaas_customer_id:
        return person.asaas_customer_id
    if not person.cpf:
        raise AsaasCheckoutError(
            "Pessoa sem CPF — obrigatório para criar cliente Asaas."
        )
    try:
        customer = asaas_client.create_customer(
            name=person.full_name,
            cpf_cnpj=person.cpf,
            email=person.email or None,
            phone=person.phone or None,
            external_reference=person.pk,
            postal_code=person.postal_code or None,
            address=person.address or None,
            address_number=person.address_number or None,
            address_complement=person.address_complement or None,
            address_neighborhood=person.address_neighborhood or None,
            city=person.city or None,
        )
    except asaas_client.AsaasClientError as exc:
        raise AsaasCheckoutError(str(exc)) from exc

    customer_id = customer.get("id") if isinstance(customer, dict) else None
    if not customer_id:
        raise AsaasCheckoutError("Resposta Asaas sem id de cliente.")
    Person.objects.filter(pk=person.pk).update(asaas_customer_id=customer_id)
    person.asaas_customer_id = customer_id
    return customer_id


@transaction.atomic
def create_pix_charge_for_order(order: RegistrationOrder):
    if order.payment_status in (
        PaymentStatus.PAID,
        PaymentStatus.EXEMPTED,
        PaymentStatus.REFUNDED,
    ):
        raise AsaasCheckoutError("Pedido já processado.")

    total = order.total or 0
    if total is None or float(total) <= 0:
        raise AsaasCheckoutError("Pedido sem valor cobrável.")

    if order.asaas_payment_id and order.asaas_pix_copy_paste:
        now = timezone.now()
        if order.asaas_pix_expires_at and order.asaas_pix_expires_at > now:
            invoice_url = ""
            try:
                existing_payment = asaas_client.get_payment(order.asaas_payment_id)
                invoice_url = existing_payment.get("invoiceUrl") or ""
            except asaas_client.AsaasClientError:
                logger.warning(
                    "Nao foi possivel recuperar invoiceUrl do PIX Asaas %s",
                    order.asaas_payment_id,
                )
            return {
                "payment_id": order.asaas_payment_id,
                "qrcode": order.asaas_pix_qrcode,
                "copy_paste": order.asaas_pix_copy_paste,
                "expires_at": order.asaas_pix_expires_at,
                "invoice_url": invoice_url,
                "reused": True,
            }

    customer_id = ensure_asaas_customer(order.person)
    due_date = timezone.localdate() + timedelta(days=settings.ASAAS_PIX_DUE_DAYS)
    description = f"Pedido #{order.pk} — {site_name()}"

    try:
        payment = asaas_client.create_pix_payment(
            customer_id=customer_id,
            value=total,
            due_date=due_date,
            description=description,
            external_reference=order.pk,
        )
    except asaas_client.AsaasClientError as exc:
        raise AsaasCheckoutError(str(exc)) from exc

    payment_id = payment.get("id")
    if not payment_id:
        raise AsaasCheckoutError("Resposta Asaas sem id do pagamento.")

    try:
        qr = asaas_client.get_pix_qrcode(payment_id)
    except asaas_client.AsaasClientError as exc:
        raise AsaasCheckoutError(str(exc)) from exc

    copy_paste = qr.get("payload") or ""
    image = qr.get("encodedImage") or ""
    expires_at = timezone.now() + timedelta(
        minutes=settings.ASAAS_PIX_EXPIRATION_MINUTES
    )

    order.asaas_payment_id = payment_id
    order.asaas_pix_copy_paste = copy_paste
    order.asaas_pix_qrcode = image
    order.asaas_pix_expires_at = expires_at
    order.save(
        update_fields=[
            "asaas_payment_id",
            "asaas_pix_copy_paste",
            "asaas_pix_qrcode",
            "asaas_pix_expires_at",
            "updated_at",
        ]
    )
    apply_order_financials(
        order,
        payment_provider=PaymentProvider.ASAAS,
        financial_transaction_id=payment_id,
    )

    return {
        "payment_id": payment_id,
        "qrcode": image,
        "copy_paste": copy_paste,
        "expires_at": expires_at,
        "invoice_url": payment.get("invoiceUrl") or "",
        "reused": False,
    }


@transaction.atomic
def create_credit_card_charge_for_order(order: RegistrationOrder, *, installment_count=None, success_url=None):
    if order.payment_status in (
        PaymentStatus.PAID,
        PaymentStatus.EXEMPTED,
        PaymentStatus.REFUNDED,
    ):
        raise AsaasCheckoutError("Pedido já processado.")

    total = order.total or 0
    if total is None or float(total) <= 0:
        raise AsaasCheckoutError("Pedido sem valor cobrável.")

    if order.asaas_payment_id:
        try:
            existing_payment = asaas_client.get_payment(order.asaas_payment_id)
        except asaas_client.AsaasClientError as exc:
            raise AsaasCheckoutError(str(exc)) from exc
        invoice_url = existing_payment.get("invoiceUrl") or ""
        if invoice_url:
            return {
                "payment_id": order.asaas_payment_id,
                "invoice_url": invoice_url,
                "reused": True,
            }

    customer_id = ensure_asaas_customer(order.person)
    due_date = timezone.localdate() + timedelta(days=settings.ASAAS_CARD_DUE_DAYS)
    description = f"Pedido #{order.pk} — {site_name()}"

    if installment_count is None:
        installment_count = _max_installments_for_order(order)

    try:
        payment = asaas_client.create_credit_card_payment(
            customer_id=customer_id,
            value=total,
            due_date=due_date,
            description=description,
            external_reference=order.pk,
            installment_count=installment_count,
            success_url=success_url,
        )
    except asaas_client.AsaasClientError as exc:
        raise AsaasCheckoutError(str(exc)) from exc

    payment_id = payment.get("id")
    invoice_url = payment.get("invoiceUrl") or ""
    if not payment_id:
        raise AsaasCheckoutError("Resposta Asaas sem id do pagamento.")
    if not invoice_url:
        raise AsaasCheckoutError("Resposta Asaas sem URL da fatura.")

    order.asaas_payment_id = payment_id
    order.save(update_fields=["asaas_payment_id", "updated_at"])
    apply_order_financials(
        order,
        payment_provider=PaymentProvider.ASAAS,
        financial_transaction_id=payment_id,
    )

    return {
        "payment_id": payment_id,
        "invoice_url": invoice_url,
        "reused": False,
    }


_CYCLE_MAX_INSTALLMENTS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}

INSTALLMENT_OPTIONS = {
    "monthly":    [1],
    "quarterly":  [1, 3],
    "semiannual": [1, 2, 3, 6],
    "annual":     [1, 2, 3, 4, 6, 12],
}


def _billing_cycle_for_order(order):
    if order.plan_id:
        return order.plan.billing_cycle
    if order.plan_price_ref_id:
        return order.plan_price_ref.billing_cycle
    return "monthly"


def _max_installments_for_order(order):
    cycle = _billing_cycle_for_order(order)
    return _CYCLE_MAX_INSTALLMENTS.get(cycle, 1)


def get_installment_options_for_order(order):
    from decimal import Decimal, ROUND_HALF_UP
    cycle = _billing_cycle_for_order(order)
    options = INSTALLMENT_OPTIONS.get(cycle, [1])
    total = Decimal(str(order.total or 0))
    cent = Decimal("0.01")
    result = []
    for n in options:
        value_per = (total / Decimal(n)).quantize(cent, rounding=ROUND_HALF_UP)
        result.append({"count": n, "value_per": value_per, "total": total})
    return result
