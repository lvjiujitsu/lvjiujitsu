from django.core.exceptions import ObjectDoesNotExist

from system.business_rule.models import (
    ClassCategory,
    ClassGroup,
    OperationalRole,
    Person,
    PersonOperationalRole,
)
from system.business_rule.models.class_membership import ClassInstructorAssignment
from system.business_rule.services.portal_capabilities import ensure_default_operational_roles
from system.business_rule.services.registration import sync_person_class_enrollments
from system.core.documents import format_cpf_digits


def enrollment_specs(entry: dict) -> list[dict]:
    specs = entry.get("class_enrollments")
    if specs:
        return list(specs)
    category_code = (entry.get("class_group_category") or "").strip()
    teacher_cpf = (entry.get("class_group_teacher_cpf") or "").strip()
    if category_code and teacher_cpf:
        return [{
            "class_group_category": category_code,
            "class_group_teacher_cpf": teacher_cpf,
        }]
    return []


def instructor_assignment_specs(entry: dict) -> list[dict]:
    specs = entry.get("class_instructor_assignments")
    if specs:
        return list(specs)
    return []


def operational_role_specs(entry: dict) -> list[dict] | None:
    if "operational_roles" not in entry:
        return None
    return list(entry.get("operational_roles") or [])


def resolve_class_group_from_spec(spec: dict) -> ClassGroup:
    category_code = spec["class_group_category"].strip()
    teacher_cpf = format_cpf_digits(spec["class_group_teacher_cpf"].strip())
    ensure_class_category_exists(category_code)
    try:
        return ClassGroup.objects.get(
            class_category__code=category_code,
            main_teacher__cpf=teacher_cpf,
        )
    except ClassGroup.DoesNotExist as exc:
        raise ObjectDoesNotExist(
            f"Turma não encontrada para categoria '{category_code}' "
            f"e professor CPF '{teacher_cpf}'. "
            "Execute 'seed_system_initial_class_catalog' depois de "
            "'seed_system_initial_teacher' antes desta seed."
        ) from exc
    except ClassGroup.MultipleObjectsReturned as exc:
        raise ObjectDoesNotExist(
            f"Múltiplas turmas para categoria '{category_code}' "
            f"e professor CPF '{teacher_cpf}'."
        ) from exc


def ensure_class_category_exists(category_code: str) -> ClassCategory:
    try:
        return ClassCategory.objects.get(code=category_code)
    except ClassCategory.DoesNotExist as exc:
        raise ObjectDoesNotExist(
            f"Categoria '{category_code}' não encontrada. "
            "Execute 'seed_system_initial_class_categories' antes desta seed."
        ) from exc


def validate_administrative_training_dependencies(entry: dict) -> None:
    category_code = (entry.get("class_category") or "").strip()
    if category_code:
        ensure_class_category_exists(category_code)
    for spec in enrollment_specs(entry):
        resolve_class_group_from_spec(spec)
    for spec in instructor_assignment_specs(entry):
        resolve_class_group_from_spec(spec)


def validate_administrative_operational_role_dependencies(entry: dict) -> None:
    specs = operational_role_specs(entry)
    if specs is None:
        return
    roles = ensure_default_operational_roles()
    for spec in specs:
        role_code = (spec.get("role_code") or "").strip()
        if not role_code:
            raise ObjectDoesNotExist("Papel operacional sem 'role_code' no JSON administrativo.")
        if role_code not in roles:
            raise ObjectDoesNotExist(f"Papel operacional '{role_code}' não cadastrado.")
        if _role_spec_has_class_group(spec):
            resolve_class_group_from_spec(spec)


def sync_administrative_operational_roles(person: Person, entry: dict) -> dict:
    specs = operational_role_specs(entry)
    if specs is None:
        return {}

    roles = ensure_default_operational_roles()
    desired_assignments = []
    for spec in specs:
        role = _resolve_operational_role(roles, spec)
        class_group = resolve_class_group_from_spec(spec) if _role_spec_has_class_group(spec) else None
        desired_assignments.append((role, class_group))

    _delete_removed_seed_roles(person, desired_assignments)
    synced_roles = []
    for role, class_group in desired_assignments:
        assignment, _ = PersonOperationalRole.objects.update_or_create(
            person=person,
            role=role,
            class_group=class_group,
            defaults={
                "is_active": True,
                "notes": _ADMINISTRATIVE_SEED_ROLE_NOTE,
            },
        )
        synced_roles.append(assignment)

    return {"operational_roles": synced_roles}


def sync_administrative_training_links(person: Person, entry: dict) -> dict:
    summary = {
        "category": None,
        "enrollment_groups": [],
        "assignment_groups": [],
    }

    category_code = (entry.get("class_category") or "").strip()
    if category_code:
        category = ensure_class_category_exists(category_code)
        if person.class_category_id != category.pk:
            person.class_category = category
            person.save(update_fields=["class_category", "updated_at"])
        summary["category"] = category.display_name

    enrollment_groups = [
        resolve_class_group_from_spec(spec) for spec in enrollment_specs(entry)
    ]
    if enrollment_specs(entry):
        sync_person_class_enrollments(person, enrollment_groups)
        summary["enrollment_groups"] = enrollment_groups

    assignment_specs = instructor_assignment_specs(entry)
    if assignment_specs:
        desired_group_ids = {
            resolve_class_group_from_spec(spec).pk for spec in assignment_specs
        }
        ClassInstructorAssignment.objects.filter(person=person).exclude(
            class_group_id__in=desired_group_ids
        ).delete()
        for spec in assignment_specs:
            group = resolve_class_group_from_spec(spec)
            ClassInstructorAssignment.objects.update_or_create(
                person=person,
                class_group=group,
                defaults={
                    "is_primary": False,
                    "notes": "Apoio administrativo na turma (seed inicial).",
                },
            )
            summary["assignment_groups"].append(group)
    else:
        ClassInstructorAssignment.objects.filter(person=person).delete()

    return summary


_ADMINISTRATIVE_SEED_ROLE_NOTE = "Seed inicial administrativa."


def _resolve_operational_role(roles: dict[str, OperationalRole], spec: dict) -> OperationalRole:
    role_code = (spec.get("role_code") or "").strip()
    try:
        return roles[role_code]
    except KeyError as exc:
        raise ObjectDoesNotExist(f"Papel operacional '{role_code}' não cadastrado.") from exc


def _role_spec_has_class_group(spec: dict) -> bool:
    return bool(
        (spec.get("class_group_category") or "").strip()
        and (spec.get("class_group_teacher_cpf") or "").strip()
    )


def _delete_removed_seed_roles(person: Person, desired_assignments: list[tuple]) -> None:
    desired_keys = {
        (role.pk, class_group.pk if class_group else None)
        for role, class_group in desired_assignments
    }
    for assignment in PersonOperationalRole.objects.filter(
        person=person,
        notes=_ADMINISTRATIVE_SEED_ROLE_NOTE,
    ):
        key = (assignment.role_id, assignment.class_group_id)
        if key not in desired_keys:
            assignment.delete()
