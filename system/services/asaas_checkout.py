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
            return {
                "payment_id": order.asaas_payment_id,
                "qrcode": order.asaas_pix_qrcode,
                "copy_paste": order.asaas_pix_copy_paste,
                "expires_at": order.asaas_pix_expires_at,
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
        "reused": False,
    }
