from system.models import AuditLog


def record_audit_log(*, category, action, actor_user=None, target=None, status=AuditLog.STATUS_SUCCESS, metadata=None, request=None):
    AuditLog.objects.create(
        actor_user=actor_user,
        category=category,
        action=action,
        status=status,
        target_model=target.__class__.__name__ if target is not None else "",
        target_uuid=getattr(target, "uuid", None),
        ip_address=_get_ip_address(request),
        user_agent=_get_user_agent(request),
        metadata=metadata or {},
    )


def _get_ip_address(request):
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request):
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")[:255]
