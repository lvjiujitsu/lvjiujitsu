import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.constants import PersonTypeCode
from system.models import Person, PersonType, PortalAccount
from system.models.graduation import BeltRank, Graduation


class Command(BaseCommand):
    help = "Cria professores iniciais a partir de static/initial_data/initial_teachers.json."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_teacher"))
        password = self._get_password()
        data = self._load_json()
        instructor_type = self._get_instructor_type()

        if not data:
            self.stdout.write(self.style.WARNING("Nenhum professor encontrado no arquivo initial_teachers.json."))
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

                person, person_created = Person.objects.get_or_create(
                    cpf=cpf,
                    defaults=self._build_person_defaults(entry, instructor_type),
                )
                if not person_created:
                    self._apply_person_updates(person, entry, instructor_type)
                    person.save()

                account, account_created = PortalAccount.objects.get_or_create(person=person)
                account.set_password(password)
                account.is_active = True
                account.save()

                graduation_count = self._sync_graduation_history(
                    person,
                    entry.get("graduation_history", []),
                )

                action = "criado" if person_created else "atualizado"
                grad_label = (
                    f", {graduation_count} graduação(ões) nova(s)"
                    if graduation_count
                    else ""
                )
                self.stdout.write(f"  [{action}] {person.full_name} (CPF {cpf}){grad_label}")
                if person_created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nProfessores: {created_count} criado(s), {updated_count} atualizado(s)."
            )
        )

    def _get_password(self) -> str:
        password = getattr(settings, "SEED_INITIAL_TEACHER_PASSWORD", "").strip()
        if not password:
            raise CommandError(
                "A configuração 'SEED_INITIAL_TEACHER_PASSWORD' não foi definida no arquivo .env."
            )
        return password

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / "initial_teachers.json"
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_instructor_type(self) -> PersonType:
        try:
            return PersonType.objects.get(code=PersonTypeCode.INSTRUCTOR)
        except PersonType.DoesNotExist:
            raise CommandError(
                "O tipo de pessoa 'instructor' não existe. "
                "Execute 'seed_system_initial_person_type' antes desta seed."
            )

    def _build_person_defaults(self, entry: dict, instructor_type: PersonType) -> dict:
        defaults = {
            "full_name": entry["full_name"].strip(),
            "person_type": instructor_type,
        }
        for field in _person_json_string_fields():
            value = entry.get(field, "")
            if value:
                defaults[field] = value
        for field in _person_json_date_fields():
            value = entry.get(field)
            if value:
                defaults[field] = value
        if entry.get("jiu_jitsu_stripes") is not None:
            defaults["jiu_jitsu_stripes"] = entry["jiu_jitsu_stripes"]
        return defaults

    def _apply_person_updates(self, person: Person, entry: dict, instructor_type: PersonType) -> None:
        person.full_name = entry["full_name"].strip()
        person.person_type = instructor_type
        for field in _person_json_string_fields():
            value = entry.get(field, "")
            if value:
                setattr(person, field, value)
        for field in _person_json_date_fields():
            value = entry.get(field)
            if value:
                setattr(person, field, value)
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
                    "Execute 'seed_system_initial_belt_ranks' antes desta seed."
                )

        existing = {
            (belt_code, grade, str(awarded_at))
            for belt_code, grade, awarded_at in person.graduations.values_list(
                "belt_rank__code",
                "grade_number",
                "awarded_at",
            )
        }
        created = 0
        for entry in history:
            key = (
                entry["belt_rank_code"],
                entry["grade_number"],
                str(entry["awarded_at"]),
            )
            if key in existing:
                continue
            Graduation.objects.create(
                person=person,
                belt_rank=belt_ranks[entry["belt_rank_code"]],
                grade_number=entry["grade_number"],
                awarded_at=entry["awarded_at"],
            )
            existing.add(key)
            created += 1
        return created


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
