import json
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.management.base import CommandError
from django.db import transaction

from system.business_rule.models import (
    BeltRank,
    ClassInstructorAssignment,
    Graduation,
    Person,
    PersonOperationalRole,
    PersonRelationship,
    PersonRelationshipKind,
    PortalAccount,
)
from system.business_rule.services.administrative_training import (
    ensure_class_category_exists,
    resolve_class_group_from_spec,
)
from system.business_rule.services.portal_capabilities import ensure_default_operational_roles
from system.business_rule.services.registration import (
    ensure_default_person_types,
    sync_person_class_enrollments,
)
from system.core.documents import format_cpf_digits


TEST_SEED_NOTE = "Seed inicial de homologacao visual."


def _portal_password() -> str:
    return str(getattr(settings, "SEED_TEST_PORTAL_PASSWORD", "") or "").strip()


REQUIRED_ENTRY_KEYS = {
    "fixture_id",
    "coverage_tags",
    "full_name",
    "cpf",
    "email",
    "phone",
    "birth_date",
    "biological_sex",
    "blood_type",
    "allergies",
    "previous_injuries",
    "emergency_contact",
    "martial_art",
    "martial_art_graduation",
    "jiu_jitsu_belt",
    "jiu_jitsu_stripes",
    "martial_art_started_at",
    "martial_art_last_graduation_at",
    "previous_academy",
    "person_type_code",
    "class_category_code",
    "class_enrollments",
    "class_instructor_assignments",
    "operational_roles",
    "relationships",
    "graduation_history",
    "is_active",
    "portal_is_active",
    "stripe_customer_id",
    "asaas_customer_id",
    "postal_code",
    "address",
    "address_number",
    "address_complement",
    "address_neighborhood",
    "city",
    "visual_validation_notes",
}


DATE_FIELDS = {
    "birth_date",
    "martial_art_started_at",
    "martial_art_last_graduation_at",
}


PERSON_UPDATE_FIELDS = {
    "full_name",
    "email",
    "phone",
    "birth_date",
    "biological_sex",
    "blood_type",
    "allergies",
    "previous_injuries",
    "emergency_contact",
    "martial_art",
    "martial_art_graduation",
    "jiu_jitsu_belt",
    "jiu_jitsu_stripes",
    "martial_art_started_at",
    "martial_art_last_graduation_at",
    "previous_academy",
    "is_active",
    "stripe_customer_id",
    "asaas_customer_id",
    "postal_code",
    "address",
    "address_number",
    "address_complement",
    "address_neighborhood",
    "city",
}


def seed_test_people_fixture(data_filename: str) -> dict:
    entries = _load_entries(data_filename)
    _validate_entries(entries, data_filename)

    try:
        with transaction.atomic():
            person_types = ensure_default_person_types()
            roles = ensure_default_operational_roles()
            _validate_dependencies(entries, person_types, roles)

            summary = {
                "people_created": 0,
                "people_updated": 0,
                "portal_accounts": 0,
                "enrollments": 0,
                "operational_roles": 0,
                "instructor_assignments": 0,
                "graduations": 0,
                "relationships": 0,
            }

            seeded_people = {}
            for entry in entries:
                person, created = _upsert_person(entry, person_types)
                seeded_people[_formatted_cpf(entry["cpf"])] = person
                summary["people_created" if created else "people_updated"] += 1
                summary["portal_accounts"] += _sync_portal_account(person, entry)
                summary["enrollments"] += _sync_class_enrollments(person, entry)
                summary["operational_roles"] += _sync_operational_roles(person, entry, roles)
                summary["instructor_assignments"] += _sync_class_instructor_assignments(
                    person,
                    entry,
                )
                summary["graduations"] += _sync_graduation_history(person, entry)

            for entry in entries:
                source_person = seeded_people[_formatted_cpf(entry["cpf"])]
                summary["relationships"] += _sync_relationships(source_person, entry)

            return summary
    except (ObjectDoesNotExist, ValueError, ValidationError) as exc:
        raise CommandError(str(exc)) from exc


def _load_entries(data_filename: str) -> list[dict]:
    path = Path(settings.BASE_DIR) / "static" / "business_rule" / "initial_data" / data_filename
    if not path.exists():
        raise CommandError(f"Arquivo nao encontrado: {path}")
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if isinstance(payload, dict):
        payload = payload.get("people")
    if not isinstance(payload, list):
        raise CommandError(f"{data_filename} deve conter uma lista JSON de pessoas.")
    return payload


def _validate_entries(entries: list[dict], data_filename: str) -> None:
    if not entries:
        raise CommandError(f"{data_filename} nao possui entradas.")
    seen_cpfs = set()
    for index, entry in enumerate(entries, start=1):
        missing = sorted(REQUIRED_ENTRY_KEYS - set(entry))
        if missing:
            raise CommandError(
                f"Entrada {index} em {data_filename} esta sem campo(s): {', '.join(missing)}"
            )
        if not str(entry["full_name"]).strip():
            raise CommandError(f"Entrada {index} em {data_filename} esta sem full_name.")
        if not _portal_password():
            raise CommandError(
                "SEED_TEST_PORTAL_PASSWORD não está configurada. Defina a "
                "variavel no arquivo de ambiente antes de rodar as seeds "
                "ficticias de homologacao."
            )
        cpf = _formatted_cpf(entry["cpf"])
        if cpf in seen_cpfs:
            raise CommandError(f"CPF duplicado em {data_filename}: {cpf}")
        seen_cpfs.add(cpf)
        _validate_list(entry, "coverage_tags", data_filename, index)
        _validate_list(entry, "class_enrollments", data_filename, index)
        _validate_list(entry, "class_instructor_assignments", data_filename, index)
        _validate_list(entry, "operational_roles", data_filename, index)
        _validate_list(entry, "relationships", data_filename, index)
        _validate_list(entry, "graduation_history", data_filename, index)


def _validate_dependencies(entries: list[dict], person_types: dict, roles: dict) -> None:
    entry_cpfs = {_formatted_cpf(entry["cpf"]) for entry in entries}
    for entry in entries:
        person_type_code = entry["person_type_code"]
        if person_type_code not in person_types:
            raise ObjectDoesNotExist(f"Tipo de pessoa '{person_type_code}' nao cadastrado.")

        category_code = entry.get("class_category_code")
        if category_code:
            ensure_class_category_exists(category_code)

        for spec in entry.get("class_enrollments", []):
            resolve_class_group_from_spec(spec)
        for spec in entry.get("class_instructor_assignments", []):
            resolve_class_group_from_spec(spec)
        for spec in entry.get("operational_roles", []):
            role_code = (spec.get("role_code") or "").strip()
            if role_code not in roles:
                raise ObjectDoesNotExist(f"Papel operacional '{role_code}' nao cadastrado.")
            if _role_spec_has_class_group(spec):
                resolve_class_group_from_spec(spec)
        for history in entry.get("graduation_history", []):
            belt_code = (history.get("belt_rank_code") or "").strip()
            if not belt_code:
                raise ObjectDoesNotExist("Historico de graduacao sem 'belt_rank_code'.")
            if not BeltRank.objects.filter(code=belt_code).exists():
                raise ObjectDoesNotExist(f"Faixa '{belt_code}' nao cadastrada.")
        for relationship in entry.get("relationships", []):
            target_cpf = _formatted_cpf(relationship["target_cpf"])
            if target_cpf in entry_cpfs:
                continue
            if not Person.objects.filter(cpf=target_cpf).exists():
                raise ObjectDoesNotExist(
                    f"Pessoa alvo '{target_cpf}' nao encontrada para relacionamento de "
                    f"{entry['fixture_id']}. Execute a seed que cria o alvo antes desta."
                )


def _upsert_person(entry: dict, person_types: dict) -> tuple[Person, bool]:
    defaults = _person_defaults(entry)
    defaults["person_type"] = person_types[entry["person_type_code"]]

    category_code = entry.get("class_category_code")
    defaults["class_category"] = (
        ensure_class_category_exists(category_code) if category_code else None
    )

    return Person.objects.update_or_create(
        cpf=_formatted_cpf(entry["cpf"]),
        defaults=defaults,
    )


def _person_defaults(entry: dict) -> dict:
    defaults = {}
    for field_name in PERSON_UPDATE_FIELDS:
        value = entry.get(field_name)
        if field_name in DATE_FIELDS:
            value = _parse_date(value, field_name, entry["fixture_id"])
        defaults[field_name] = value
    return defaults


def _sync_portal_account(person: Person, entry: dict) -> int:
    account, _ = PortalAccount.objects.get_or_create(
        person=person,
        defaults={"password_hash": ""},
    )
    account.set_password(_portal_password())
    account.is_active = bool(entry.get("portal_is_active", True))
    account.save()
    return 1


def _sync_class_enrollments(person: Person, entry: dict) -> int:
    specs = entry.get("class_enrollments", [])
    groups = [resolve_class_group_from_spec(spec) for spec in specs]
    sync_person_class_enrollments(person, groups)
    return len(groups)


def _sync_operational_roles(person: Person, entry: dict, roles: dict) -> int:
    desired = []
    for spec in entry.get("operational_roles", []):
        role = roles[(spec.get("role_code") or "").strip()]
        class_group = resolve_class_group_from_spec(spec) if _role_spec_has_class_group(spec) else None
        desired.append((role, class_group))

    desired_keys = {
        (role.pk, class_group.pk if class_group else None)
        for role, class_group in desired
    }
    for assignment in PersonOperationalRole.objects.filter(person=person, notes=TEST_SEED_NOTE):
        key = (assignment.role_id, assignment.class_group_id)
        if key not in desired_keys:
            assignment.delete()

    for role, class_group in desired:
        PersonOperationalRole.objects.update_or_create(
            person=person,
            role=role,
            class_group=class_group,
            defaults={
                "is_active": True,
                "notes": TEST_SEED_NOTE,
            },
        )
    return len(desired)


def _sync_class_instructor_assignments(person: Person, entry: dict) -> int:
    groups = [
        resolve_class_group_from_spec(spec)
        for spec in entry.get("class_instructor_assignments", [])
    ]
    desired_group_ids = {group.pk for group in groups}
    for assignment in ClassInstructorAssignment.objects.filter(person=person, notes=TEST_SEED_NOTE):
        if assignment.class_group_id not in desired_group_ids:
            assignment.delete()

    for group in groups:
        ClassInstructorAssignment.objects.update_or_create(
            person=person,
            class_group=group,
            defaults={
                "is_primary": False,
                "notes": TEST_SEED_NOTE,
            },
        )
    return len(groups)


def _sync_graduation_history(person: Person, entry: dict) -> int:
    count = 0
    for history in entry.get("graduation_history", []):
        belt_rank = BeltRank.objects.get(code=history["belt_rank_code"])
        awarded_at = _parse_date(history["awarded_at"], "awarded_at", entry["fixture_id"])
        Graduation.objects.update_or_create(
            person=person,
            belt_rank=belt_rank,
            grade_number=history.get("grade_number", 0),
            awarded_at=awarded_at,
            defaults={
                "notes": history.get("notes") or TEST_SEED_NOTE,
            },
        )
        count += 1
    return count


def _sync_relationships(source_person: Person, entry: dict) -> int:
    relationships = entry.get("relationships", [])
    desired_target_cpfs = {
        _formatted_cpf(relationship["target_cpf"])
        for relationship in relationships
    }
    for relationship in PersonRelationship.objects.filter(
        source_person=source_person,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        notes=TEST_SEED_NOTE,
    ):
        if relationship.target_person.cpf not in desired_target_cpfs:
            relationship.delete()

    for relationship in relationships:
        target_person = Person.objects.get(cpf=_formatted_cpf(relationship["target_cpf"]))
        PersonRelationship.objects.update_or_create(
            source_person=source_person,
            target_person=target_person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            defaults={
                "kinship_type": relationship.get("kinship_type", ""),
                "kinship_other_label": relationship.get("kinship_other_label", ""),
                "notes": relationship.get("notes") or TEST_SEED_NOTE,
            },
        )
    return len(relationships)


def _validate_list(entry: dict, key: str, data_filename: str, index: int) -> None:
    if not isinstance(entry.get(key), list):
        raise CommandError(
            f"Entrada {index} em {data_filename} precisa ter '{key}' como lista."
        )


def _formatted_cpf(value: str) -> str:
    return format_cpf_digits(str(value))


def _parse_date(value, field_name: str, fixture_id: str) -> date | None:
    if value in ("", None):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise CommandError(
            f"Data invalida em {fixture_id}.{field_name}: {value}"
        ) from exc


def _role_spec_has_class_group(spec: dict) -> bool:
    return bool(
        (spec.get("class_group_category") or "").strip()
        and (spec.get("class_group_teacher_cpf") or "").strip()
    )
