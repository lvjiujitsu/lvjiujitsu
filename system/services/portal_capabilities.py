from system.constants import (
    DEFAULT_OPERATIONAL_ROLE_DEFINITIONS,
    PERSON_TYPE_CAPABILITIES,
)
from system.models import OperationalRole


def ensure_default_operational_roles() -> dict[str, OperationalRole]:
    roles = {}
    for code, defaults in DEFAULT_OPERATIONAL_ROLE_DEFINITIONS.items():
        role, _ = OperationalRole.objects.update_or_create(
            code=code,
            defaults={
                "display_name": defaults["display_name"],
                "description": defaults["description"],
                "capabilities": defaults["capabilities"],
                "is_active": True,
            },
        )
        roles[code] = role
    return roles


def get_person_operational_role_codes(person) -> set[str]:
    return {
        assignment.role.code
        for assignment in _active_operational_role_assignments(person)
    }


def get_person_capabilities(person) -> set[str]:
    capabilities = set()
    if person is None:
        return capabilities

    if person.person_type_id:
        capabilities.update(PERSON_TYPE_CAPABILITIES.get(person.person_type.code, ()))

    for assignment in _active_operational_role_assignments(person):
        capabilities.update(assignment.role.capabilities or [])
    return capabilities


def person_has_any_capability(person, *capabilities: str) -> bool:
    return bool(set(capabilities) & get_person_capabilities(person))


def get_operational_role_labels(person) -> list[str]:
    labels = []
    seen_codes = set()
    for assignment in _active_operational_role_assignments(person):
        role = assignment.role
        if role.code in seen_codes:
            continue
        labels.append(role.display_name)
        seen_codes.add(role.code)
    return labels


def _active_operational_role_assignments(person):
    if person is None:
        return []

    cached = getattr(person, "_prefetched_objects_cache", {}).get(
        "operational_role_assignments"
    )
    if cached is not None:
        return [
            assignment
            for assignment in cached
            if assignment.is_active and assignment.role.is_active
        ]

    return list(
        person.operational_role_assignments.select_related("role", "class_group").filter(
            is_active=True,
            role__is_active=True,
        )
    )
