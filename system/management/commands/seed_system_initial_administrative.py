import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_date

from system.constants import PersonTypeCode
from system.models import ClassCategory, Person, PersonType, PortalAccount
from system.models.graduation import BeltRank, Graduation
from system.services.administrative_training import (
    sync_administrative_operational_roles,
    sync_administrative_training_links,
    validate_administrative_operational_role_dependencies,
    validate_administrative_training_dependencies,
)


class Command(BaseCommand):
    help = "Cria usuários administrativos iniciais a partir de static/initial_data/initial_administrative.json."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_administrative"))
        password = self._get_password()
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(
                "Nenhum usuário encontrado no arquivo initial_administrative.json."
            ))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                cpf = entry.get("cpf", "").strip()
                full_name = entry.get("full_name", "").strip()
                if not cpf or not full_name:
                    raise CommandError(
                        f"Entrada inválida no JSON: 'cpf' e 'full_name' são obrigatórios. Entrada: {entry}"
                    )

                person_type = self._get_person_type(entry)
                self._validate_operational_role_dependencies(entry)
                self._validate_training_dependencies(entry)
                person, person_created = Person.objects.get_or_create(
                    cpf=cpf,
                    defaults=self._build_person_defaults(entry, person_type),
                )
                if not person_created:
                    self._apply_person_updates(person, entry, person_type)
                    person.save()

                account, _ = PortalAccount.objects.get_or_create(person=person)
                account.set_password(password)
                account.is_active = True
                account.save()

                graduation_count = self._sync_graduation_history(person, entry.get("graduation_history", []))
                operational_summary = self._sync_operational_roles(person, entry)
                training_summary = self._sync_training_links(person, entry)

                action = "criado" if person_created else "atualizado"
                grad_label = f", {graduation_count} graduação(ões) registrada(s)" if graduation_count else ""
                operational_label = self._format_operational_summary(operational_summary)
                training_label = self._format_training_summary(training_summary)
                self.stdout.write(
                    f"  [{action}] {person.full_name} (CPF {cpf}){grad_label}{operational_label}{training_label}"
                )

                if person_created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nAdministrativos: {created_count} criado(s), {updated_count} atualizado(s)."
            )
        )

    def _get_password(self) -> str:
        password = getattr(settings, "SEED_INITIAL_ADMINISTRATIVE_PASSWORD", "").strip()
        if not password:
            raise CommandError(
                "A configuração 'SEED_INITIAL_ADMINISTRATIVE_PASSWORD' não foi definida no arquivo .env."
            )
        return password

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / "initial_administrative.json"
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_person_type(self, entry: dict) -> PersonType:
        code = (entry.get("person_type") or PersonTypeCode.ADMINISTRATIVE_ASSISTANT).strip()
        try:
            return PersonType.objects.get(code=code)
        except PersonType.DoesNotExist:
            raise CommandError(
                f"O tipo de pessoa '{code}' não existe. "
                "Execute 'seed_system_initial_person_type' antes desta seed."
            )

    def _build_person_defaults(self, entry: dict, person_type: PersonType) -> dict:
        defaults = {
            "full_name": entry["full_name"].strip(),
            "person_type": person_type,
        }
        for field in _person_json_string_fields():
            value = entry.get(field, "")
            if value:
                defaults[field] = value
        for field in _person_json_date_fields():
            value = entry.get(field)
            parsed = _parse_json_date(value)
            if parsed:
                defaults[field] = parsed
        if entry.get("jiu_jitsu_stripes") is not None:
            defaults["jiu_jitsu_stripes"] = entry["jiu_jitsu_stripes"]
        return defaults

    def _apply_person_updates(self, person: Person, entry: dict, person_type: PersonType) -> None:
        person.full_name = entry["full_name"].strip()
        person.person_type = person_type
        for field in _person_json_string_fields():
            value = entry.get(field, "")
            if value:
                setattr(person, field, value)
        for field in _person_json_date_fields():
            value = entry.get(field)
            parsed = _parse_json_date(value)
            if parsed:
                setattr(person, field, parsed)
        if entry.get("jiu_jitsu_stripes") is not None:
            person.jiu_jitsu_stripes = entry["jiu_jitsu_stripes"]

    def _sync_graduation_history(self, person: Person, history: list) -> int:
        if not history:
            return 0

        belt_rank_codes = {entry["belt_rank_code"] for entry in history}
        belt_ranks = {}
        for code in belt_rank_codes:
            try:
                belt_ranks[code] = BeltRank.objects.get(code=code)
            except BeltRank.DoesNotExist:
                raise CommandError(
                    f"Faixa '{code}' não encontrada. "
                    "Execute a seed de faixas antes desta seed."
                )

        existing = set(
            person.graduations.values_list("belt_rank__code", "grade_number", "awarded_at")
        )

        created = 0
        for entry in history:
            key = (entry["belt_rank_code"], entry["grade_number"], entry["awarded_at"] if isinstance(entry["awarded_at"], type(None)) else str(entry["awarded_at"]))
            # Normalize to date string for comparison
            awarded_at_str = str(entry["awarded_at"])
            already_exists = any(
                str(belt_rank_code) == entry["belt_rank_code"]
                and grade == entry["grade_number"]
                and str(awarded) == awarded_at_str
                for belt_rank_code, grade, awarded in existing
            )
            if not already_exists:
                Graduation.objects.create(
                    person=person,
                    belt_rank=belt_ranks[entry["belt_rank_code"]],
                    grade_number=entry["grade_number"],
                    awarded_at=entry["awarded_at"],
                )
                created += 1
        return created

    def _sync_training_links(self, person: Person, entry: dict) -> dict:
        if not (
            entry.get("class_category")
            or entry.get("class_enrollments")
            or entry.get("class_group_category")
            or entry.get("class_instructor_assignments")
        ):
            return {}
        try:
            return sync_administrative_training_links(person, entry)
        except (ObjectDoesNotExist, ClassCategory.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc

    def _sync_operational_roles(self, person: Person, entry: dict) -> dict:
        try:
            return sync_administrative_operational_roles(person, entry)
        except ObjectDoesNotExist as exc:
            raise CommandError(str(exc)) from exc

    def _validate_operational_role_dependencies(self, entry: dict) -> None:
        try:
            validate_administrative_operational_role_dependencies(entry)
        except ObjectDoesNotExist as exc:
            raise CommandError(str(exc)) from exc

    def _validate_training_dependencies(self, entry: dict) -> None:
        if not (
            entry.get("class_category")
            or entry.get("class_enrollments")
            or entry.get("class_group_category")
            or entry.get("class_instructor_assignments")
        ):
            return
        try:
            validate_administrative_training_dependencies(entry)
        except (ObjectDoesNotExist, ClassCategory.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc

    def _format_operational_summary(self, summary: dict) -> str:
        assignments = summary.get("operational_roles") if summary else None
        if not assignments:
            return ""
        labels = []
        for assignment in assignments:
            label = assignment.role.display_name
            if assignment.class_group_id:
                label = (
                    f"{label}: {assignment.class_group.display_name}/"
                    f"{assignment.class_group.class_category.display_name}"
                )
            labels.append(label)
        return f" (papéis: {', '.join(labels)})"

    def _format_training_summary(self, summary: dict) -> str:
        if not summary:
            return ""
        parts = []
        if summary.get("category"):
            parts.append(f"categoria {summary['category']}")
        if summary.get("enrollment_groups"):
            labels = ", ".join(
                f"{group.display_name}/{group.class_category.display_name}"
                for group in summary["enrollment_groups"]
            )
            parts.append(f"matrículas: {labels}")
        if summary.get("assignment_groups"):
            labels = ", ".join(
                f"{group.display_name}/{group.class_category.display_name}"
                for group in summary["assignment_groups"]
            )
            parts.append(f"apoio: {labels}")
        return f" ({'; '.join(parts)})" if parts else ""


def _person_json_string_fields():
    return (
        "email",
        "phone",
        "biological_sex",
        "blood_type",
        "allergies",
        "previous_injuries",
        "emergency_contact",
        "martial_art",
        "martial_art_graduation",
        "jiu_jitsu_belt",
        "previous_academy",
    )


def _person_json_date_fields():
    return (
        "birth_date",
        "martial_art_started_at",
        "martial_art_last_graduation_at",
    )


def _parse_json_date(value):
    if not value:
        return None
    if hasattr(value, "year"):
        return value
    parsed = parse_date(str(value))
    if parsed is None:
        raise CommandError(f"Data inválida no JSON administrativo: {value!r}")
    return parsed
