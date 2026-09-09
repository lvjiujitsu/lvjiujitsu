import logging

from django.conf import settings
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from system.core.password_reset.registry import adapter_for, registered_kinds

INTERNAL_RESET_URL_TOKEN = "set-password"
INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"
RESET_RETURN_SESSION_KEY = "password_reset_return_url"
RESET_EMAIL_SUBJECT_TEMPLATE = "core/emails/password_reset_subject.txt"
RESET_EMAIL_BODY_TEMPLATE = "core/emails/password_reset_body.txt"

logger = logging.getLogger("django.contrib.auth")


class AccountTokenGenerator(PasswordResetTokenGenerator):

    def __init__(self, kind, adapter):
        super().__init__()
        self.kind = kind
        self.adapter = adapter

    def _make_hash_value(self, account, timestamp):
        return (
            f"{self.kind}{account.pk}"
            f"{self.adapter.password_hash(account)}{timestamp}"
        )


def account_is_reachable(adapter, account):
    if not adapter.is_active(account):
        return False
    if not adapter.email(account):
        return False
    return is_password_usable(adapter.password_hash(account))


def find_resettable_account(lookup_value):
    value = (lookup_value or "").strip()
    if not value:
        return None, None
    for kind, adapter in registered_kinds():
        account = adapter.find(value)
        if account is not None and account_is_reachable(adapter, account):
            return kind, account
    return None, None


def make_reset_credentials(kind, account):
    adapter = adapter_for(kind)
    identifier = urlsafe_base64_encode(force_bytes(f"{kind}:{account.pk}"))
    return identifier, AccountTokenGenerator(kind, adapter).make_token(account)


def resolve_reset_credentials(identifier, token):
    if not identifier or not token:
        return None
    try:
        decoded = force_str(urlsafe_base64_decode(identifier))
        kind, raw_pk = decoded.split(":", 1)
    except (ValueError, TypeError, UnicodeDecodeError):
        return None
    adapter = adapter_for(kind)
    if adapter is None:
        return None
    try:
        account = adapter.get(raw_pk)
    except (ValueError, TypeError, ValidationError):
        return None
    if account is None or not account_is_reachable(adapter, account):
        return None
    if not AccountTokenGenerator(kind, adapter).check_token(account, token):
        return None
    return kind, account


def set_account_password(kind, account, raw_password):
    adapter_for(kind).set_password(account, raw_password)


def password_reset_done_context(request):
    return {
        "login_url": request.session.pop(
            RESET_RETURN_SESSION_KEY, settings.LOGIN_URL
        )
    }


def remember_return_url(request, kind, account):
    request.session[RESET_RETURN_SESSION_KEY] = adapter_for(kind).login_url(account)


def send_password_reset_email(kind, account, base_url):
    adapter = adapter_for(kind)
    identifier, token = make_reset_credentials(kind, account)
    path = reverse("system:password-reset-confirm", args=[identifier, token])
    recipient = adapter.email(account)
    context = {
        "name": adapter.display_name(account),
        "reset_url": f"{base_url.rstrip('/')}{path}",
        "site_name": settings.SITE_NAME,
        "reset_timeout_hours": settings.PASSWORD_RESET_TIMEOUT // 3600,
    }
    subject = render_to_string(RESET_EMAIL_SUBJECT_TEMPLATE, context)
    body = render_to_string(RESET_EMAIL_BODY_TEMPLATE, context)
    message = EmailMessage(
        subject=" ".join(subject.split()),
        body=body,
        to=[recipient],
    )
    try:
        message.send()
    except Exception:
        logger.exception("Falha ao enviar o e-mail de redefinição de senha para %s", recipient)
    return context["reset_url"]
