from system.business_rule.constants import Capability


CLASS_CATALOG_DECISION_CAPABILITIES = (
    Capability.MANAGE_CLASSES,
    Capability.MANAGE_ACADEMY,
)


def can_decide_class_catalog_request(request_capabilities):
    return bool(set(CLASS_CATALOG_DECISION_CAPABILITIES) & set(request_capabilities))


def can_cancel_class_catalog_request(catalog_request, *, actor, actor_capabilities):
    if can_decide_class_catalog_request(actor_capabilities):
        return True
    if actor is None:
        return False
    return actor.pk in (catalog_request.requester_person_id, catalog_request.teacher_person_id)
