from system.models import AuthenticationEvent
from system.models import AuditLog
from system.services.reports.audit import record_audit_log


def record_authentication_event(event_type, request, actor_user=None, identifier="", metadata=None):
    AuthenticationEvent.objects.create(
        actor_user=actor_user,
        identifier=identifier,
        event_type=event_type,
        ip_address=_get_ip_address(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        metadata=metadata or {},
    )
    record_audit_log(
        category=AuditLog.CATEGORY_AUTH,
        action=event_type,
        actor_user=actor_user,
        status=_resolve_audit_status(event_type),
        metadata={"identifier": identifier, **(metadata or {})},
        request=request,
    )


def _get_ip_address(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _resolve_audit_status(event_type):
    if event_type == AuthenticationEvent.EVENT_LOGIN_FAILURE:
        return AuditLog.STATUS_FAILURE
    return AuditLog.STATUS_SUCCESS
