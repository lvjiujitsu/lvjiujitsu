from system.core.access import identity_of
from system.core.audit.models import AuditEntry

SYSTEM_ACTOR_LABEL = "sistema"

_actor_label_resolver = None


def register_actor_label_resolver(resolver):
    global _actor_label_resolver
    _actor_label_resolver = resolver


def actor_label(source):
    if source is None:
        return SYSTEM_ACTOR_LABEL
    if hasattr(source, "identity"):
        identity = identity_of(source)
        return identity.label if identity.authenticated else SYSTEM_ACTOR_LABEL
    if isinstance(source, str):
        return source or SYSTEM_ACTOR_LABEL
    if _actor_label_resolver is not None:
        return _actor_label_resolver(source) or SYSTEM_ACTOR_LABEL
    return str(source)


def record_event(source, action, module, entity_label, summary=""):
    return AuditEntry.objects.create(
        module=module[:40],
        action=action[:30],
        actor_label=actor_label(source)[:150],
        entity_label=entity_label[:200],
        summary=summary[:300],
    )
