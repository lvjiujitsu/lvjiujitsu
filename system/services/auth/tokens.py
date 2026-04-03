import logging

from django.utils import timezone

from system.constants import PASSWORD_ACTION_FIRST_ACCESS, PASSWORD_ACTION_RESET
from system.models import AuthenticationEvent, PasswordActionToken, SystemUser
from system.services.auth.audit import record_authentication_event
from system.services.auth.cpf import normalize_cpf


logger = logging.getLogger(__name__)


def issue_password_action_token(request, cpf, purpose):
    normalized_cpf = normalize_cpf(cpf)
    if not normalized_cpf:
        record_authentication_event(
            AuthenticationEvent.EVENT_LOGIN_FAILURE,
            request,
            identifier=str(cpf),
            metadata={"reason": "invalid_cpf_for_token"},
        )
        return None
    try:
        user = SystemUser.objects.get(cpf=normalized_cpf)
    except SystemUser.DoesNotExist:
        record_authentication_event(
            _request_event_for(purpose),
            request,
            identifier=normalized_cpf,
            metadata={"issued": False},
        )
        return None
    if not user.is_active:
        record_authentication_event(
            _request_event_for(purpose),
            request,
            actor_user=user,
            identifier=normalized_cpf,
            metadata={"issued": False, "reason": "inactive_user"},
        )
        return None

    PasswordActionToken.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).update(used_at=timezone.now())

    token = PasswordActionToken.issue(user=user, purpose=purpose)
    record_authentication_event(
        _request_event_for(purpose),
        request,
        actor_user=user,
        identifier=user.cpf,
        metadata={"issued": True},
    )
    logger.info("password action token issued for %s with purpose %s: %s", user.cpf, purpose, token.token)
    return token


def get_usable_password_action_token(token_value, purpose):
    try:
        token = PasswordActionToken.objects.select_related("user").get(token=token_value, purpose=purpose)
    except PasswordActionToken.DoesNotExist:
        return None
    if not token.is_usable:
        return None
    return token


def consume_password_action_token(request, token, raw_password):
    user = token.user
    user.set_password(raw_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password", "updated_at"])
    token.mark_used()
    record_authentication_event(
        _success_event_for(token.purpose),
        request,
        actor_user=user,
        identifier=user.cpf,
        metadata={"token_uuid": str(token.uuid)},
    )
    return user


def _request_event_for(purpose):
    if purpose == PASSWORD_ACTION_FIRST_ACCESS:
        return AuthenticationEvent.EVENT_FIRST_ACCESS_REQUEST
    return AuthenticationEvent.EVENT_PASSWORD_RESET_REQUEST


def _success_event_for(purpose):
    if purpose == PASSWORD_ACTION_FIRST_ACCESS:
        return AuthenticationEvent.EVENT_FIRST_ACCESS_SUCCESS
    return AuthenticationEvent.EVENT_PASSWORD_RESET_SUCCESS

