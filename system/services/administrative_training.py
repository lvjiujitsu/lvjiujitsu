from django.core.exceptions import ObjectDoesNotExist

from system.models import ClassCategory, ClassGroup, Person
from system.models.class_membership import ClassInstructorAssignment
from system.services.registration import sync_person_class_enrollments
from system.utils.person_data import format_cpf_digits


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


def resolve_class_group_from_spec(spec: dict) -> ClassGroup:
    category_code = spec["class_group_category"].strip()
    teacher_cpf = format_cpf_digits(spec["class_group_teacher_cpf"].strip())
    try:
        return ClassGroup.objects.get(
            class_category__code=category_code,
            main_teacher__cpf=teacher_cpf,
        )
    except ClassGroup.DoesNotExist as exc:
        raise ObjectDoesNotExist(
            f"Turma não encontrada para categoria '{category_code}' "
            f"e professor CPF '{teacher_cpf}'."
        ) from exc
    except ClassGroup.MultipleObjectsReturned as exc:
        raise ObjectDoesNotExist(
            f"Múltiplas turmas para categoria '{category_code}' "
            f"e professor CPF '{teacher_cpf}'."
        ) from exc


def sync_administrative_training_links(person: Person, entry: dict) -> dict:
    summary = {
        "category": None,
        "enrollment_groups": [],
        "assignment_groups": [],
    }

    category_code = (entry.get("class_category") or "").strip()
    if category_code:
        category = ClassCategory.objects.get(code=category_code)
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
