from system.core.access import identity_of
from system.core.audit import SYSTEM_ACTOR_LABEL
from system.core.audit import record_event as record_audit_entry


def actor_label_for(source):
    if source is None:
        return SYSTEM_ACTOR_LABEL
    if hasattr(source, "identity"):
        identity = identity_of(source)
        return identity.label if identity.authenticated else SYSTEM_ACTOR_LABEL
    if isinstance(source, str):
        return source or SYSTEM_ACTOR_LABEL
    person = getattr(source, "person", None)
    return person.full_name if person is not None else str(source)


def record_event(source, action, module, entity_label, summary=""):
    return record_audit_entry(
        module=module,
        action=action,
        actor_label=actor_label_for(source),
        entity=module,
        entity_label=entity_label,
        summary=summary,
    )
