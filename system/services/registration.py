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
        profile = cleaned_data["registration_profile"]
        if profile == "holder":
            return _create_holder_registration(cleaned_data, person_types)
        if profile == "guardian":
            return _create_guardian_registration(cleaned_data, person_types)
        return _create_other_registration(cleaned_data, person_types)


def ensure_default_person_types():
    return {code: _get_or_create_person_type(code) for code in DEFAULT_PERSON_TYPE_DEFINITIONS}


def get_kinship_choices():
    return KINSHIP_TYPE_CHOICES


def parse_extra_dependents_payload(raw_payload):
    if not raw_payload:
        return []
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


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


def _get_or_create_person_type(code):
    defaults = DEFAULT_PERSON_TYPE_DEFINITIONS[code]
    person_type, _ = PersonType.objects.update_or_create(code=code, defaults=defaults)
    return person_type


def _create_holder_registration(cleaned_data, person_types):
    holder = _create_person_with_account(
        full_name=cleaned_data["holder_name"],
        cpf=cleaned_data["holder_cpf"],
        email=cleaned_data.get("holder_email", ""),
        phone=cleaned_data.get("holder_phone", ""),
        birth_date=cleaned_data.get("holder_birthdate"),
        password=cleaned_data["holder_password"],
        person_type=person_types["student"],
        blood_type=cleaned_data.get("holder_blood_type", ""),
        allergies=cleaned_data.get("holder_allergies", ""),
        previous_injuries=cleaned_data.get("holder_injuries", ""),
        emergency_contact=cleaned_data.get("holder_emergency_contact", ""),
        class_category=cleaned_data.get("holder_class_category"),
        class_group=cleaned_data.get("holder_class_group"),
        class_schedule=cleaned_data.get("holder_class_schedule"),
    )
    created_people = {"holder": holder}

    if not cleaned_data.get("include_dependent"):
        return created_people

    dependents = _build_primary_dependent_payload(cleaned_data, "dependent")
    dependents.extend(cleaned_data.get("extra_dependents", []))

    created_dependents = []
    for index, dependent_payload in enumerate(dependents, start=1):
        dependent = _create_person_with_account(
            full_name=dependent_payload["full_name"],
            cpf=dependent_payload["cpf"],
            email=dependent_payload.get("email", ""),
            phone=dependent_payload.get("phone", ""),
            birth_date=dependent_payload.get("birth_date"),
            password=dependent_payload["password"],
            person_type=person_types["dependent"],
            blood_type=dependent_payload.get("blood_type", ""),
            allergies=dependent_payload.get("allergies", ""),
            previous_injuries=dependent_payload.get("previous_injuries", ""),
            emergency_contact=dependent_payload.get("emergency_contact", ""),
            class_category=dependent_payload.get("class_category"),
            class_group=dependent_payload.get("class_group"),
            class_schedule=dependent_payload.get("class_schedule"),
        )
        _create_relationship(
            source_person=holder,
            target_person=dependent,
            kinship_type=dependent_payload.get("kinship_type", ""),
            kinship_other_label=dependent_payload.get("kinship_other_label", ""),
        )
        created_dependents.append(dependent)
        if index == 1:
            created_people["dependent"] = dependent

    created_people["dependents"] = created_dependents
    return created_people


def _create_guardian_registration(cleaned_data, person_types):
    guardian = _create_person_with_account(
        full_name=cleaned_data["guardian_name"],
        cpf=cleaned_data["guardian_cpf"],
        email=cleaned_data.get("guardian_email", ""),
        phone=cleaned_data.get("guardian_phone", ""),
        password=cleaned_data["guardian_password"],
        person_type=person_types["guardian"],
    )

    dependents = _build_primary_dependent_payload(cleaned_data, "student")
    dependents.extend(cleaned_data.get("extra_dependents", []))

    created_people = {"guardian": guardian}
    created_dependents = []
    for index, dependent_payload in enumerate(dependents, start=1):
        dependent = _create_person_with_account(
            full_name=dependent_payload["full_name"],
            cpf=dependent_payload["cpf"],
            email=dependent_payload.get("email", ""),
            phone=dependent_payload.get("phone", ""),
            birth_date=dependent_payload.get("birth_date"),
            password=dependent_payload["password"],
            person_type=person_types["dependent"],
            blood_type=dependent_payload.get("blood_type", ""),
            allergies=dependent_payload.get("allergies", ""),
            previous_injuries=dependent_payload.get("previous_injuries", ""),
            emergency_contact=dependent_payload.get("emergency_contact", ""),
            class_category=dependent_payload.get("class_category"),
            class_group=dependent_payload.get("class_group"),
            class_schedule=dependent_payload.get("class_schedule"),
        )
        _create_relationship(
            source_person=guardian,
            target_person=dependent,
            kinship_type=dependent_payload.get("kinship_type", ""),
            kinship_other_label=dependent_payload.get("kinship_other_label", ""),
        )
        created_dependents.append(dependent)
        if index == 1:
            created_people["student"] = dependent

    created_people["dependents"] = created_dependents
    return created_people


def _create_other_registration(cleaned_data, person_types):
    other_type_code = cleaned_data.get("other_type_code")
    if not other_type_code:
        raise ValueError("Tipo de cadastro ausente para o perfil Outro.")

    other_person = _create_person_with_account(
        full_name=cleaned_data["other_name"],
        cpf=cleaned_data["other_cpf"],
        email=cleaned_data.get("other_email", ""),
        phone=cleaned_data.get("other_phone", ""),
        birth_date=cleaned_data.get("other_birthdate"),
        password=cleaned_data["other_password"],
        person_type=person_types[other_type_code],
        class_category=cleaned_data.get("other_class_category"),
        class_group=cleaned_data.get("other_class_group"),
        class_schedule=cleaned_data.get("other_class_schedule"),
    )
    return {"other": other_person}


def _create_person_with_account(
    *,
    full_name,
    cpf,
    password,
    person_type,
    email="",
    phone="",
    birth_date=None,
    blood_type="",
    allergies="",
    previous_injuries="",
    emergency_contact="",
    class_category=None,
    class_group=None,
    class_schedule=None,
):
    person = Person.objects.create(
        full_name=full_name,
        cpf=cpf,
        email=email,
        phone=phone,
        birth_date=birth_date,
        blood_type=blood_type,
        allergies=allergies,
        previous_injuries=previous_injuries,
        emergency_contact=emergency_contact,
        person_type=person_type,
        class_category=derive_class_category(
            class_group=class_group,
            explicit_category=class_category,
        ),
        class_group=class_group,
        class_schedule=class_schedule,
    )
    access_account = PortalAccount(person=person)
    access_account.set_password(password)
    access_account.save()
    return person


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
