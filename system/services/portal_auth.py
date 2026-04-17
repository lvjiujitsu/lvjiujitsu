from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from system.models import PortalAccount, PortalPasswordResetToken
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.services.membership import get_latest_open_order
from system.services.trial_access import has_active_trial_for_person
from system.utils import ensure_formatted_cpf, only_digits


User = get_user_model()

PORTAL_ACCOUNT_SESSION_KEY = "portal_account_id"
TECHNICAL_ADMIN_SESSION_KEY = "technical_admin_user_id"


def authenticate_portal_identity(identifier: str, password: str):
    access_account = _authenticate_local_portal_account(identifier, password)
    if access_account is not None:
        pending_order = get_latest_open_order(access_account.person)
        if pending_order is not None and not has_active_trial_for_person(
            access_account.person
        ):
            return {
                "blocked_reason": "payment_pending",
                "pending_order": pending_order,
                "portal_account": access_account,
            }
        return {"portal_account": access_account, "technical_admin_user": None}

    technical_admin_user = _authenticate_technical_admin(identifier, password)
    if technical_admin_user is not None:
        return {"portal_account": None, "technical_admin_user": technical_admin_user}

    return None


def has_pending_payment(person) -> bool:
    return get_latest_open_order(person) is not None


def login_portal_identity(request, *, portal_account=None, technical_admin_user=None) -> None:
    request.session.cycle_key()
    request.session.pop(PORTAL_ACCOUNT_SESSION_KEY, None)
    request.session.pop(TECHNICAL_ADMIN_SESSION_KEY, None)

    request.portal_account = None
    request.portal_person = None
    request.technical_admin_user = None

    if portal_account is not None:
        request.session[PORTAL_ACCOUNT_SESSION_KEY] = portal_account.pk
        request.portal_account = portal_account
        request.portal_person = portal_account.person

    if technical_admin_user is not None:
        request.session[TECHNICAL_ADMIN_SESSION_KEY] = technical_admin_user.pk
        request.technical_admin_user = technical_admin_user


def logout_portal_identity(request) -> None:
    request.session.pop(PORTAL_ACCOUNT_SESSION_KEY, None)
    request.session.pop(TECHNICAL_ADMIN_SESSION_KEY, None)
    request.portal_account = None
    request.portal_person = None
    request.technical_admin_user = None


def resolve_portal_account_from_session(request):
    access_account_id = request.session.get(PORTAL_ACCOUNT_SESSION_KEY)
    if not access_account_id:
        return None

    access_account = (
        PortalAccount.objects.select_related("person")
        .filter(pk=access_account_id, is_active=True, person__is_active=True)
        .first()
    )

    if access_account is None:
        request.session.pop(PORTAL_ACCOUNT_SESSION_KEY, None)

    return access_account


def resolve_technical_admin_from_session(request):
    technical_admin_user_id = request.session.get(TECHNICAL_ADMIN_SESSION_KEY)
    if not technical_admin_user_id:
        return None

    technical_admin_user = (
        User.objects.filter(pk=technical_admin_user_id, is_active=True)
        .filter(is_staff=True)
        .first()
    )

    if technical_admin_user is None:
        request.session.pop(TECHNICAL_ADMIN_SESSION_KEY, None)

    return technical_admin_user


def create_password_reset_token(cpf: str, request) -> None:
    formatted_cpf = ensure_formatted_cpf(cpf)
    access_account = _get_active_account_by_cpf(formatted_cpf)

    if access_account is None or not access_account.person.email:
        return

    now = timezone.now()
    PortalPasswordResetToken.objects.filter(
        access_account=access_account,
        used_at__isnull=True,
        expires_at__gt=now,
    ).update(used_at=now, updated_at=now)

    reset_token = PortalPasswordResetToken.objects.create(
        access_account=access_account,
    )
    reset_url = request.build_absolute_uri(
        reverse("system:password-reset-confirm", kwargs={"token": reset_token.token})
    )
    message = (
        f"Olá, {access_account.person.full_name}.\n\n"
        f"Use o link abaixo para redefinir sua senha do portal LV JIU JITSU:\n\n"
        f"{reset_url}\n\n"
        "Se você não solicitou esta alteração, ignore este e-mail."
    )
    send_mail(
        subject="Redefinição de senha - LV JIU JITSU",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[access_account.person.email],
        fail_silently=False,
    )


def get_valid_password_reset_token(token: str):
    reset_token = (
        PortalPasswordResetToken.objects.select_related("access_account", "access_account__person")
        .filter(token=token)
        .first()
    )

    if reset_token is None or not reset_token.is_valid():
        return None

    return reset_token


def reset_portal_password(reset_token: PortalPasswordResetToken, new_password: str) -> None:
    access_account = reset_token.access_account
    access_account.set_password(new_password)
    access_account.failed_login_attempts = 0
    access_account.save(
        update_fields=("password_hash", "password_updated_at", "failed_login_attempts", "updated_at")
    )
    reset_token.mark_as_used()
    now = timezone.now()
    PortalPasswordResetToken.objects.filter(
        access_account=access_account,
        used_at__isnull=True,
        expires_at__gt=now,
    ).exclude(pk=reset_token.pk).update(used_at=now, updated_at=now)


def _authenticate_local_portal_account(identifier: str, password: str):
    formatted_cpf = _normalize_cpf_identifier(identifier)
    if formatted_cpf is None:
        return None

    access_account = _get_active_account_by_cpf(formatted_cpf)
    if access_account is None:
        return None

    if access_account.check_password(password):
        access_account.register_successful_login()
        return access_account

    access_account.register_failed_login()
    return None


def _authenticate_technical_admin(identifier: str, password: str):
    technical_admin_user = authenticate(username=identifier, password=password)
    if technical_admin_user is None:
        return None
    if not (technical_admin_user.is_superuser or technical_admin_user.is_staff):
        return None
    return technical_admin_user


def _normalize_cpf_identifier(identifier: str):
    digits = only_digits(identifier)
    if len(digits) != 11:
        return None
    return ensure_formatted_cpf(identifier)


def _get_active_account_by_cpf(formatted_cpf: str):
    return (
        PortalAccount.objects.select_related("person")
        .filter(person__cpf=formatted_cpf, is_active=True, person__is_active=True)
        .first()
    )
