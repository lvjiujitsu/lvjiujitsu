import json

from django.db import transaction

from system.models import (
    ClassCategory,
    ClassGroup,
    ClassSchedule,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PortalAccount,
)


DEFAULT_PERSON_TYPE_DEFINITIONS = {
    "student": {
        "display_name": "Aluno",
        "description": "Pessoa com matrícula ativa como aluno.",
    },
    "guardian": {
        "display_name": "Responsável",
        "description": "Pessoa responsável por um aluno ou dependente.",
    },
    "dependent": {
        "display_name": "Dependente",
        "description": "Pessoa vinculada a um titular ou responsável.",
    },
    "instructor": {
        "display_name": "Professor",
        "description": "Pessoa vinculada ao corpo docente.",
    },
    "administrative-assistant": {
        "display_name": "Administrativo",
        "description": "Pessoa vinculada ao apoio administrativo.",
    },
}

KINSHIP_TYPE_CHOICES = (
    ("father", "Pai"),
    ("mother", "Mãe"),
    ("uncle", "Tio"),
    ("stepchild", "Enteado"),
    ("other", "Outro"),
)


def create_portal_registration(cleaned_data):
    with transaction.atomic():
        person_types = ensure_default_person_types()
        student_type = person_types["student"]
        guardian_type = person_types["guardian"]
        dependent_type = person_types["dependent"]

        profile = cleaned_data["registration_profile"]
        if profile == "holder":
            return _create_holder_registration(
                cleaned_data,
                student_type,
                guardian_type,
                dependent_type,
            )
        if profile == "guardian":
            return _create_guardian_registration(
                cleaned_data,
                student_type,
                guardian_type,
                dependent_type,
            )
        return _create_other_registration(cleaned_data)


def ensure_default_person_types():
    return {
        code: _get_or_create_person_type(code)
        for code in DEFAULT_PERSON_TYPE_DEFINITIONS
    }


def get_kinship_choices():
    return KINSHIP_TYPE_CHOICES


def _get_or_create_person_type(code):
    defaults = DEFAULT_PERSON_TYPE_DEFINITIONS[code]
    person_type, _ = PersonType.objects.update_or_create(code=code, defaults=defaults)
    return person_type


def _create_holder_registration(cleaned_data, student_type, guardian_type, dependent_type):
    holder = _create_person_with_account(
        full_name=cleaned_data["holder_name"],
        cpf=cleaned_data["holder_cpf"],
        email=cleaned_data.get("holder_email", ""),
        phone=cleaned_data.get("holder_phone", ""),
        birth_date=cleaned_data.get("holder_birthdate"),
        password=cleaned_data["holder_password"],
        blood_type=cleaned_data.get("holder_blood_type", ""),
        allergies=cleaned_data.get("holder_allergies", ""),
        previous_injuries=cleaned_data.get("holder_injuries", ""),
        emergency_contact=cleaned_data.get("holder_emergency_contact", ""),
        class_category=cleaned_data.get("holder_class_category"),
        class_group=cleaned_data.get("holder_class_group"),
        class_schedule=cleaned_data.get("holder_class_schedule"),
    )
    holder.person_types.add(student_type)

    created_people = {"holder": holder}

    dependents = []
    if cleaned_data.get("include_dependent"):
        holder.person_types.add(guardian_type)
        dependents.extend(_build_primary_dependent_payload(cleaned_data, "dependent"))
        dependents.extend(cleaned_data.get("extra_dependents", []))

    for index, dependent_payload in enumerate(dependents, start=1):
        dependent = _create_person_with_account(
            full_name=dependent_payload["full_name"],
            cpf=dependent_payload["cpf"],
            email=dependent_payload.get("email", ""),
            phone=dependent_payload.get("phone", ""),
            birth_date=dependent_payload.get("birth_date"),
            password=dependent_payload["password"],
            blood_type=dependent_payload.get("blood_type", ""),
            allergies=dependent_payload.get("allergies", ""),
            previous_injuries=dependent_payload.get("previous_injuries", ""),
            emergency_contact=dependent_payload.get("emergency_contact", ""),
            class_category=dependent_payload.get("class_category"),
            class_group=dependent_payload.get("class_group"),
            class_schedule=dependent_payload.get("class_schedule"),
        )
        dependent.person_types.add(student_type, dependent_type)
        _create_relationship(
            source_person=holder,
            target_person=dependent,
            kinship_type=dependent_payload.get("kinship_type", ""),
            kinship_other_label=dependent_payload.get("kinship_other_label", ""),
        )
        if index == 1:
            created_people["dependent"] = dependent
        dependents[index - 1]["instance"] = dependent

    if dependents:
        created_people["dependents"] = [item["instance"] for item in dependents]

    return created_people


def _create_guardian_registration(cleaned_data, student_type, guardian_type, dependent_type):
    guardian = _create_person_with_account(
        full_name=cleaned_data["guardian_name"],
        cpf=cleaned_data["guardian_cpf"],
        email=cleaned_data.get("guardian_email", ""),
        phone=cleaned_data.get("guardian_phone", ""),
        password=cleaned_data["guardian_password"],
    )
    guardian.person_types.add(guardian_type)

    dependents = []
    dependents.extend(_build_primary_dependent_payload(cleaned_data, "student"))
    dependents.extend(cleaned_data.get("extra_dependents", []))

    created_people = {"guardian": guardian}
    for index, dependent_payload in enumerate(dependents, start=1):
        student = _create_person_with_account(
            full_name=dependent_payload["full_name"],
            cpf=dependent_payload["cpf"],
            email=dependent_payload.get("email", ""),
            phone=dependent_payload.get("phone", ""),
            birth_date=dependent_payload.get("birth_date"),
            password=dependent_payload["password"],
            blood_type=dependent_payload.get("blood_type", ""),
            allergies=dependent_payload.get("allergies", ""),
            previous_injuries=dependent_payload.get("previous_injuries", ""),
            emergency_contact=dependent_payload.get("emergency_contact", ""),
            class_category=dependent_payload.get("class_category"),
            class_group=dependent_payload.get("class_group"),
            class_schedule=dependent_payload.get("class_schedule"),
        )
        student.person_types.add(student_type, dependent_type)

        _create_relationship(
            source_person=guardian,
            target_person=student,
            kinship_type=dependent_payload.get("kinship_type", ""),
            kinship_other_label=dependent_payload.get("kinship_other_label", ""),
        )
        if index == 1:
            created_people["student"] = student
        dependents[index - 1]["instance"] = student

    created_people["dependents"] = [item["instance"] for item in dependents]
    return created_people


def _create_other_registration(cleaned_data):
    other_person = _create_person_with_account(
        full_name=cleaned_data["other_name"],
        cpf=cleaned_data["other_cpf"],
        email=cleaned_data.get("other_email", ""),
        phone=cleaned_data.get("other_phone", ""),
        birth_date=cleaned_data.get("other_birthdate"),
        password=cleaned_data["other_password"],
        class_category=cleaned_data.get("other_class_category"),
        class_group=cleaned_data.get("other_class_group"),
        class_schedule=cleaned_data.get("other_class_schedule"),
    )

    if cleaned_data.get("other_type_codes"):
        selected_person_types = PersonType.objects.filter(
            is_active=True,
            code__in=cleaned_data["other_type_codes"],
        )
        other_person.person_types.set(selected_person_types)

    return {"other": other_person}


def _create_person_with_account(**kwargs):
    class_group = kwargs.get("class_group")
    class_category = kwargs.get("class_category") or derive_class_category(
        class_group=class_group
    )
    person = Person.objects.create(
        full_name=kwargs["full_name"],
        cpf=kwargs["cpf"],
        email=kwargs.get("email", ""),
        phone=kwargs.get("phone", ""),
        birth_date=kwargs.get("birth_date"),
        blood_type=kwargs.get("blood_type", ""),
        allergies=kwargs.get("allergies", ""),
        previous_injuries=kwargs.get("previous_injuries", ""),
        emergency_contact=kwargs.get("emergency_contact", ""),
        class_category=class_category,
        class_group=class_group,
        class_schedule=kwargs.get("class_schedule"),
    )
    access_account = PortalAccount(person=person)
    access_account.set_password(kwargs["password"])
    access_account.save()
    return person


def parse_extra_dependents_payload(raw_payload):
    if not raw_payload:
        return []
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return payload


def resolve_class_category(category_id):
    if not category_id:
        return None
    return ClassCategory.objects.filter(pk=category_id, is_active=True).first()


def resolve_class_group(group_id):
    if not group_id:
        return None
    return ClassGroup.objects.filter(pk=group_id, is_active=True).first()


def resolve_class_schedule(schedule_id):
    if not schedule_id:
        return None
    return ClassSchedule.objects.filter(pk=schedule_id, is_active=True).first()


def derive_class_category(*, class_group=None, explicit_category=None):
    if explicit_category is not None:
        return explicit_category
    if class_group is not None:
        return class_group.class_category
    return None


def _build_primary_dependent_payload(cleaned_data, prefix):
    name = cleaned_data.get(f"{prefix}_name")
    if not name:
        return []

    return [
        {
            "full_name": cleaned_data.get(f"{prefix}_name"),
            "cpf": cleaned_data.get(f"{prefix}_cpf"),
            "birth_date": cleaned_data.get(f"{prefix}_birthdate"),
            "password": cleaned_data.get(f"{prefix}_password"),
            "email": cleaned_data.get(f"{prefix}_email", ""),
            "phone": cleaned_data.get(f"{prefix}_phone", ""),
            "blood_type": cleaned_data.get(f"{prefix}_blood_type", ""),
            "allergies": cleaned_data.get(f"{prefix}_allergies", ""),
            "previous_injuries": cleaned_data.get(f"{prefix}_injuries", ""),
            "emergency_contact": cleaned_data.get(f"{prefix}_emergency_contact", ""),
            "class_category": cleaned_data.get(f"{prefix}_class_category"),
            "class_group": cleaned_data.get(f"{prefix}_class_group"),
            "class_schedule": cleaned_data.get(f"{prefix}_class_schedule"),
            "kinship_type": cleaned_data.get(f"{prefix}_kinship_type", ""),
            "kinship_other_label": cleaned_data.get(f"{prefix}_kinship_other_label", ""),
        }
    ]


def _create_relationship(
    *,
    source_person,
    target_person,
    kinship_type="",
    kinship_other_label="",
):
    return PersonRelationship.objects.create(
        source_person=source_person,
        target_person=target_person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        kinship_type=kinship_type,
        kinship_other_label=kinship_other_label,
    )
