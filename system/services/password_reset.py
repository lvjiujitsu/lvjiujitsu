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

from system.models import PortalAccount
from system.utils import ensure_formatted_cpf

INTERNAL_RESET_URL_TOKEN = "set-password"
INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"
RESET_EMAIL_SUBJECT_TEMPLATE = "login/emails/password_reset_subject.txt"
RESET_EMAIL_BODY_TEMPLATE = "login/emails/password_reset_body.txt"

RESETTABLE_KINDS = (("portal", PortalAccount),)
KIND_MODELS = dict(RESETTABLE_KINDS)

logger = logging.getLogger("django.contrib.auth")


class AccountTokenGenerator(PasswordResetTokenGenerator):

    def __init__(self, kind):
        super().__init__()
        self.kind = kind

    def _make_hash_value(self, account, timestamp):
        return f"{self.kind}{account.pk}{account_password_hash(account)}{timestamp}"


def account_password_hash(account):
    return account.password_hash


def account_email(account):
    return (account.person.email or "").strip()


def account_display_name(account):
    return account.person.full_name or account_email(account)


def account_is_active(account):
    return bool(account.is_active and account.person.is_active)


def set_account_password(account, raw_password):
    account.set_password(raw_password)
    account.failed_login_attempts = 0
    account.save(
        update_fields=(
            "password_hash",
            "password_updated_at",
            "failed_login_attempts",
            "updated_at",
        )
    )


def find_resettable_account(lookup_value):
    try:
        formatted_cpf = ensure_formatted_cpf((lookup_value or "").strip())
    except ValueError:
        return None, None
    for kind, model in RESETTABLE_KINDS:
        account = (
            model.objects.select_related("person")
            .filter(person__cpf=formatted_cpf)
            .first()
        )
        if account is not None and account_is_reachable(account):
            return kind, account
    return None, None


def record_password_reset(request, kind, account):
    return None


def password_reset_done_context(request):
    return {}


def account_is_reachable(account):
    if not account_is_active(account):
        return False
    if not account_email(account):
        return False
    return is_password_usable(account_password_hash(account))


def make_reset_credentials(kind, account):
    identifier = urlsafe_base64_encode(force_bytes(f"{kind}:{account.pk}"))
    return identifier, AccountTokenGenerator(kind).make_token(account)


def resolve_reset_credentials(identifier, token):
    if not identifier or not token:
        return None
    try:
        decoded = force_str(urlsafe_base64_decode(identifier))
        kind, raw_pk = decoded.split(":", 1)
    except (ValueError, TypeError, UnicodeDecodeError):
        return None
    model = KIND_MODELS.get(kind)
    if model is None:
        return None
    try:
        account = model.objects.select_related("person").filter(pk=raw_pk).first()
    except (ValueError, TypeError, ValidationError):
        return None
    if account is None or not account_is_reachable(account):
        return None
    if not AccountTokenGenerator(kind).check_token(account, token):
        return None
    return kind, account


def send_password_reset_email(kind, account, base_url):
    identifier, token = make_reset_credentials(kind, account)
    path = reverse("system:password-reset-confirm", args=[identifier, token])
    recipient = account_email(account)
    context = {
        "name": account_display_name(account),
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
        logger.exception("Failed to send password reset email to %s", recipient)
    return context["reset_url"]
