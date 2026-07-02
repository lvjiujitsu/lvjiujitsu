from system.models import OperationalAuditEntry


def record_audit_event(*, module, action, actor_label, entity_label, summary=""):
    return OperationalAuditEntry.objects.create(
        module=module,
        action=action,
        actor_label=actor_label,
        entity_label=entity_label,
        summary=summary,
    )


def resolve_actor_label(request):
    person = getattr(request, "portal_person", None)
    if person is not None:
        return person.full_name
    user = getattr(request, "technical_admin_user", None)
    if user is not None:
        return user.get_short_name() or user.get_full_name() or user.get_username()
    return "Sistema"
