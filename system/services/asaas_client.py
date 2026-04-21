import logging
from decimal import Decimal

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class AsaasClientError(Exception):
    def __init__(self, message, *, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _headers():
    if not settings.ASAAS_API_KEY:
        raise AsaasClientError("ASAAS_API_KEY não configurada no .env")
    return {
        "access_token": settings.ASAAS_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": settings.ASAAS_USER_AGENT,
    }


def _base_url():
    if not settings.ASAAS_API_URL:
        raise AsaasClientError("ASAAS_API_URL não configurada no .env")
    return settings.ASAAS_API_URL.rstrip("/")


def _request(method, path, *, json_body=None, params=None, timeout=None):
    url = f"{_base_url()}{path}"
    if timeout is None:
        timeout = settings.ASAAS_API_TIMEOUT_SECONDS
    try:
        response = requests.request(
            method,
            url,
            headers=_headers(),
            json=json_body,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        logger.exception("Falha de rede chamando Asaas %s %s", method, path)
        raise AsaasClientError(f"Erro de rede Asaas: {exc}") from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}

    if response.status_code >= 400:
        logger.error(
            "Asaas %s %s => %s: %s",
            method,
            path,
            response.status_code,
            payload,
        )
        raise AsaasClientError(
            f"Asaas retornou {response.status_code}",
            status_code=response.status_code,
            payload=payload,
        )
    return payload


def create_customer(*, name, cpf_cnpj, email=None, phone=None, external_reference=None):
    body = {"name": name, "cpfCnpj": cpf_cnpj}
    if email:
        body["email"] = email
    if phone:
        body["phone"] = phone
    if external_reference is not None:
        body["externalReference"] = str(external_reference)
    return _request("POST", "/customers", json_body=body)


def get_customer(customer_id):
    return _request("GET", f"/customers/{customer_id}")


def create_pix_payment(
    *,
    customer_id,
    value,
    due_date,
    description="",
    external_reference=None,
):
    body = {
        "customer": customer_id,
        "billingType": "PIX",
        "value": float(Decimal(value)),
        "dueDate": due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date),
    }
    if description:
        body["description"] = description[:500]
    if external_reference is not None:
        body["externalReference"] = str(external_reference)
    return _request("POST", "/payments", json_body=body)


def get_payment(payment_id):
    return _request("GET", f"/payments/{payment_id}")


def get_pix_qrcode(payment_id):
    return _request("GET", f"/payments/{payment_id}/pixQrCode")


def create_transfer(*, value, pix_key, pix_key_type, description="", external_reference=None):
    body = {
        "value": float(Decimal(value)),
        "pixAddressKey": pix_key,
        "pixAddressKeyType": pix_key_type,
        "operationType": "PIX",
    }
    if description:
        body["description"] = description[:500]
    if external_reference is not None:
        body["externalReference"] = str(external_reference)
    return _request("POST", "/transfers", json_body=body)


def get_transfer(transfer_id):
    return _request("GET", f"/transfers/{transfer_id}")


def get_balance():
    return _request("GET", "/finance/balance")


def verify_webhook_token(received_token):
    expected = settings.ASAAS_WEBHOOK_TOKEN or ""
    if not expected:
        raise AsaasClientError("ASAAS_WEBHOOK_TOKEN não configurado no .env")
    return bool(received_token) and received_token == expected
