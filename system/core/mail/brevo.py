import json
import urllib.error
import urllib.request
from email.utils import parseaddr

import django
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

BREVO_SEND_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
BREVO_ACCOUNT_ENDPOINT = "https://api.brevo.com/v3/account"


class EmailDeliveryError(Exception):

    def __init__(self, message, status=None, code=""):
        super().__init__(message)
        self.status = status
        self.code = code


def brevo_api_key():
    key = settings.BREVO_API_KEY.strip()
    if not key:
        raise EmailDeliveryError(
            "BREVO_API_KEY é obrigatória para o backend de e-mail da Brevo."
        )
    return key


def brevo_headers(key):
    return {
        "api-key": key,
        "accept": "application/json",
        "content-type": "application/json",
        "User-Agent": f"{settings.SITE_NAME}/Django-{django.get_version()}",
    }


def describe_http_error(error):
    try:
        payload = json.loads(error.read().decode("utf-8", "replace"))
    except (ValueError, OSError):
        return "", ""
    return payload.get("code", ""), payload.get("message", "")


def call_brevo(url, key, payload=None):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=brevo_headers(key),
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        code, message = describe_http_error(exc)
        detail = f": {message}" if message else "."
        raise EmailDeliveryError(
            f"A Brevo recusou a chamada com HTTP {exc.code}{detail}",
            status=exc.code,
            code=code,
        ) from exc
    except urllib.error.URLError as exc:
        raise EmailDeliveryError("A Brevo está inalcançável.") from exc
    except json.JSONDecodeError as exc:
        raise EmailDeliveryError("A Brevo respondeu fora do formato esperado.") from exc


def as_contact(address):
    name, email = parseaddr(address)
    contact = {"email": email or address}
    if name:
        contact["name"] = name
    return contact


def build_brevo_payload(message):
    payload = {
        "sender": as_contact(message.from_email or settings.DEFAULT_FROM_EMAIL),
        "to": [as_contact(address) for address in message.to],
        "subject": message.subject,
        "textContent": message.body,
    }
    if message.cc:
        payload["cc"] = [as_contact(address) for address in message.cc]
    if message.bcc:
        payload["bcc"] = [as_contact(address) for address in message.bcc]
    payload["replyTo"] = as_contact(
        message.reply_to[0]
        if message.reply_to
        else (message.from_email or settings.DEFAULT_FROM_EMAIL)
    )
    for alternative in getattr(message, "alternatives", ()):
        content, mimetype = alternative[0], alternative[1]
        if mimetype == "text/html":
            payload["htmlContent"] = content
    return payload


def check_brevo_account():
    account = call_brevo(BREVO_ACCOUNT_ENDPOINT, brevo_api_key())
    plan = account.get("plan") or []
    credits = next(
        (entry.get("credits") for entry in plan if entry.get("type") == "free"), None
    )
    if credits is None:
        return "aceita"
    return "crédito disponível" if credits > 0 else "sem crédito"


class BrevoEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        try:
            key = brevo_api_key()
        except EmailDeliveryError:
            if self.fail_silently:
                return 0
            raise
        delivered = 0
        for message in email_messages:
            if not message.to:
                continue
            try:
                call_brevo(BREVO_SEND_ENDPOINT, key, build_brevo_payload(message))
            except EmailDeliveryError:
                if not self.fail_silently:
                    raise
                continue
            delivered += 1
        return delivered
