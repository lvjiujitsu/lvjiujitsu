from django.db import transaction

from system.models import Person, PersonRelationship, PersonRelationshipKind, PersonType, PortalAccount


DEFAULT_PERSON_TYPE_DEFINITIONS = {
    "student": {
        "display_name": "Aluno",
        "description": "Pessoa com matricula ativa como aluno.",
    },
    "guardian": {
        "display_name": "Responsável",
        "description": "Pessoa responsavel por um aluno ou dependente.",
    },
    "dependent": {
        "display_name": "Dependente",
        "description": "Pessoa vinculada a um titular ou responsavel.",
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
    )
    holder.person_types.add(student_type)

    created_people = {"holder": holder}

    if cleaned_data.get("include_dependent"):
        holder.person_types.add(guardian_type)
        dependent = _create_person_with_account(
            full_name=cleaned_data["dependent_name"],
            cpf=cleaned_data["dependent_cpf"],
            birth_date=cleaned_data.get("dependent_birthdate"),
            password=cleaned_data["dependent_password"],
            blood_type=cleaned_data.get("dependent_blood_type", ""),
            allergies=cleaned_data.get("dependent_allergies", ""),
            previous_injuries=cleaned_data.get("dependent_injuries", ""),
            emergency_contact=cleaned_data.get("dependent_emergency_contact", ""),
        )
        dependent.person_types.add(student_type, dependent_type)
        PersonRelationship.objects.create(
            source_person=holder,
            target_person=dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        created_people["dependent"] = dependent

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

    student = _create_person_with_account(
        full_name=cleaned_data["student_name"],
        cpf=cleaned_data["student_cpf"],
        birth_date=cleaned_data.get("student_birthdate"),
        password=cleaned_data["student_password"],
        blood_type=cleaned_data.get("student_blood_type", ""),
        allergies=cleaned_data.get("student_allergies", ""),
        previous_injuries=cleaned_data.get("student_injuries", ""),
        emergency_contact=cleaned_data.get("student_emergency_contact", ""),
    )
    student.person_types.add(student_type, dependent_type)

    PersonRelationship.objects.create(
        source_person=guardian,
        target_person=student,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    )

    return {
        "guardian": guardian,
        "student": student,
    }


def _create_other_registration(cleaned_data):
    other_person = _create_person_with_account(
        full_name=cleaned_data["other_name"],
        cpf=cleaned_data["other_cpf"],
        email=cleaned_data.get("other_email", ""),
        phone=cleaned_data.get("other_phone", ""),
        birth_date=cleaned_data.get("other_birthdate"),
        password=cleaned_data["other_password"],
    )

    if cleaned_data.get("other_type_codes"):
        selected_person_types = PersonType.objects.filter(
            is_active=True,
            code__in=cleaned_data["other_type_codes"],
        )
        other_person.person_types.set(selected_person_types)

    return {"other": other_person}


def _create_person_with_account(**kwargs):
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
    )
    access_account = PortalAccount(person=person)
    access_account.set_password(kwargs["password"])
    access_account.save()
    return person
