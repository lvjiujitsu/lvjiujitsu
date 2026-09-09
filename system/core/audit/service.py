from system.core.audit.models import AuditEntry

SYSTEM_ACTOR_LABEL = "sistema"


def record_event(*, module, action, actor_label, entity, entity_label, summary=""):
    return AuditEntry.objects.create(
        module=module[:40],
        action=action[:30],
        actor_label=actor_label[:150],
        entity=entity[:40],
        entity_label=entity_label[:200],
        summary=summary[:300],
    )
