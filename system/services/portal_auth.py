from django.contrib.auth import authenticate, get_user_model
from django.db.models import Prefetch

from system.models import PersonOperationalRole, PortalAccount
from system.models.registration_order import PaymentStatus, RegistrationOrder
from system.services.membership import get_latest_open_order
from system.services.trial_access import has_active_trial_for_person
from system.utils import ensure_formatted_cpf, only_digits


User = get_user_model()

PORTAL_ACCOUNT_SESSION_KEY = "portal_account_id"
TECHNICAL_ADMIN_SESSION_KEY = "technical_admin_user_id"
FORCED_PASSWORD_CHANGE_SESSION_KEY = "forced_password_change_account_id"
DEFAULT_TEMP_PASSWORD = "LV@123"


def authenticate_portal_identity(identifier: str, password: str):
    access_account = _authenticate_local_portal_account(identifier, password)
    if access_account is not None:
        if access_account.check_password(DEFAULT_TEMP_PASSWORD):
            return {"blocked_reason": "must_change_password", "portal_account": access_account}
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
        _portal_account_queryset()
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


def change_own_password(access_account: PortalAccount, new_password: str) -> None:
    access_account.set_password(new_password)
    access_account.failed_login_attempts = 0
    access_account.save(
        update_fields=("password_hash", "password_updated_at", "failed_login_attempts", "updated_at")
    )


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
        _portal_account_queryset()
        .filter(person__cpf=formatted_cpf, is_active=True, person__is_active=True)
        .first()
    )


def _portal_account_queryset():
    return PortalAccount.objects.select_related(
        "person",
        "person__person_type",
    ).prefetch_related(
        Prefetch(
            "person__operational_role_assignments",
            queryset=PersonOperationalRole.objects.select_related(
                "role",
                "class_group",
            ).filter(
                is_active=True,
                role__is_active=True,
            ),
        )
    )
