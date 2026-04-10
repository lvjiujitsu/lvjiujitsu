import json

from django.db import transaction

from system.services.class_overview import resolve_class_group_selection
from system.services.registration_checkout import create_registration_order
from system.models import (
    ClassEnrollment,
    EnrollmentStatus,
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
            result = _create_holder_registration(cleaned_data, person_types)
            create_registration_order(result["holder"], cleaned_data)
            return result
        if profile == "guardian":
            result = _create_guardian_registration(cleaned_data, person_types)
            create_registration_order(result["guardian"], cleaned_data)
            return result
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


def resolve_class_groups(group_ids):
    return resolve_class_group_selection(group_ids)


def sync_person_class_enrollments(person, class_groups):
    selected_groups = class_groups or []
    if not selected_groups:
        ClassEnrollment.objects.filter(person=person).delete()
        _sync_person_membership_snapshot(person, [])
        return
    selected_group_ids = [group.pk for group in selected_groups]
    ClassEnrollment.objects.filter(person=person).exclude(
        class_group_id__in=selected_group_ids
    ).delete()
    for class_group in selected_groups:
        ClassEnrollment.objects.update_or_create(
            person=person,
            class_group=class_group,
            defaults={"status": EnrollmentStatus.ACTIVE, "notes": ""},
        )
    _sync_person_membership_snapshot(person, selected_groups)


def _sync_person_membership_snapshot(person, class_groups):
    primary_group = class_groups[0] if class_groups else None
    person.class_category = primary_group.class_category if primary_group else None
    person.class_group = primary_group
    person.class_schedule = None
    if person.pk:
        person.save(
            update_fields=(
                "class_category",
                "class_group",
                "class_schedule",
                "updated_at",
            )
        )


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
        biological_sex=cleaned_data.get("holder_biological_sex", ""),
        password=cleaned_data["holder_password"],
        person_type=person_types["student"],
        blood_type=cleaned_data.get("holder_blood_type", ""),
        allergies=cleaned_data.get("holder_allergies", ""),
        previous_injuries=cleaned_data.get("holder_injuries", ""),
        emergency_contact=cleaned_data.get("holder_emergency_contact", ""),
        martial_art=cleaned_data.get("holder_martial_art", ""),
        martial_art_graduation=cleaned_data.get("holder_martial_art_graduation", ""),
        jiu_jitsu_belt=cleaned_data.get("holder_jiu_jitsu_belt", ""),
        jiu_jitsu_stripes=cleaned_data.get("holder_jiu_jitsu_stripes"),
        class_groups=cleaned_data.get("holder_class_groups", []),
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
            biological_sex=dependent_payload.get("biological_sex", ""),
            password=dependent_payload["password"],
            person_type=person_types["dependent"],
            blood_type=dependent_payload.get("blood_type", ""),
            allergies=dependent_payload.get("allergies", ""),
            previous_injuries=dependent_payload.get("previous_injuries", ""),
            emergency_contact=dependent_payload.get("emergency_contact", ""),
            martial_art=dependent_payload.get("martial_art", ""),
            martial_art_graduation=dependent_payload.get("martial_art_graduation", ""),
            jiu_jitsu_belt=dependent_payload.get("jiu_jitsu_belt", ""),
            jiu_jitsu_stripes=dependent_payload.get("jiu_jitsu_stripes"),
            class_groups=dependent_payload.get("class_groups", []),
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
        biological_sex=cleaned_data.get("guardian_biological_sex", ""),
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
            biological_sex=dependent_payload.get("biological_sex", ""),
            password=dependent_payload["password"],
            person_type=person_types["dependent"],
            blood_type=dependent_payload.get("blood_type", ""),
            allergies=dependent_payload.get("allergies", ""),
            previous_injuries=dependent_payload.get("previous_injuries", ""),
            emergency_contact=dependent_payload.get("emergency_contact", ""),
            martial_art=dependent_payload.get("martial_art", ""),
            martial_art_graduation=dependent_payload.get("martial_art_graduation", ""),
            jiu_jitsu_belt=dependent_payload.get("jiu_jitsu_belt", ""),
            jiu_jitsu_stripes=dependent_payload.get("jiu_jitsu_stripes"),
            class_groups=dependent_payload.get("class_groups", []),
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
        biological_sex=cleaned_data.get("other_biological_sex", ""),
        password=cleaned_data["other_password"],
        person_type=person_types[other_type_code],
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
    biological_sex="",
    blood_type="",
    allergies="",
    previous_injuries="",
    emergency_contact="",
    martial_art="",
    martial_art_graduation="",
    jiu_jitsu_belt="",
    jiu_jitsu_stripes=None,
    class_category=None,
    class_groups=None,
):
    primary_group = _get_primary_class_group(class_groups)
    person = Person.objects.create(
        full_name=full_name,
        cpf=cpf,
        email=email,
        phone=phone,
        birth_date=birth_date,
        biological_sex=biological_sex,
        blood_type=blood_type,
        allergies=allergies,
        previous_injuries=previous_injuries,
        emergency_contact=emergency_contact,
        martial_art=martial_art,
        martial_art_graduation=martial_art_graduation,
        jiu_jitsu_belt=jiu_jitsu_belt,
        jiu_jitsu_stripes=jiu_jitsu_stripes,
        person_type=person_type,
        class_category=primary_group.class_category if primary_group else class_category,
        class_group=primary_group,
        class_schedule=None,
    )
    sync_person_class_enrollments(person, class_groups)
    access_account = PortalAccount(person=person)
    access_account.set_password(password)
    access_account.save()
    return person


def _get_primary_class_group(class_groups):
    if not class_groups:
        return None
    return class_groups[0]


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
            "biological_sex": cleaned_data.get(f"{prefix}_biological_sex", ""),
            "blood_type": cleaned_data.get(f"{prefix}_blood_type", ""),
            "allergies": cleaned_data.get(f"{prefix}_allergies", ""),
            "previous_injuries": cleaned_data.get(f"{prefix}_injuries", ""),
            "emergency_contact": cleaned_data.get(f"{prefix}_emergency_contact", ""),
            "martial_art": cleaned_data.get(f"{prefix}_martial_art", ""),
            "martial_art_graduation": cleaned_data.get(f"{prefix}_martial_art_graduation", ""),
            "jiu_jitsu_belt": cleaned_data.get(f"{prefix}_jiu_jitsu_belt", ""),
            "jiu_jitsu_stripes": cleaned_data.get(f"{prefix}_jiu_jitsu_stripes"),
            "class_groups": cleaned_data.get(f"{prefix}_class_groups", []),
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
