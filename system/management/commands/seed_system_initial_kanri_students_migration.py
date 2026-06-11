import json
import unicodedata
from collections import Counter
from datetime import date
from json import JSONDecodeError
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    JiuJitsuBelt,
    MartialArt,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
)
from system.models.graduation import BeltRank, Graduation
from system.utils.person_data import format_cpf_digits, only_digits


DATA_DIRNAME = "kanri_students_migration"
MIGRATION_CPF_PREFIX = "KANRI-"
PLACEHOLDER_VALUES = {"carregando", "carregando..."}

PERSON_BELT_BY_RANK_CODE = {
    "adult-white": JiuJitsuBelt.WHITE,
    "adult-blue": JiuJitsuBelt.BLUE,
    "adult-purple": JiuJitsuBelt.PURPLE,
    "adult-brown": JiuJitsuBelt.BROWN,
    "adult-black": JiuJitsuBelt.BLACK,
    "adult-coral-redblack": JiuJitsuBelt.RED_BLACK,
    "adult-coral-redwhite": JiuJitsuBelt.RED_WHITE,
    "adult-red": JiuJitsuBelt.RED,
}


class Command(BaseCommand):
    help = (
        "Importa alunos, responsáveis, dependentes e graduações a partir dos JSONs "
        f"em static/initial_data/{DATA_DIRNAME}/."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_kanri_students_migration"))

        records = self._load_records()
        if not records:
            self.stdout.write(
                self.style.WARNING(f"Nenhum arquivo JSON encontrado em {DATA_DIRNAME}.")
            )
            return

        person_types = self._get_person_types()
        student_document_counts = Counter(
            record["student_document"]
            for record in records
            if record["student_document"]
        )
        belt_ranks = self._get_belt_ranks(records)
        stats = self._empty_stats()

        with transaction.atomic():
            for record in records:
                self._sync_record(
                    record=record,
                    person_types=person_types,
                    student_document_counts=student_document_counts,
                    belt_ranks=belt_ranks,
                    stats=stats,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "\nKanri: "
                f"{stats['persons_created']} pessoa(s) criada(s), "
                f"{stats['persons_updated']} pessoa(s) atualizada(s), "
                f"{stats['relationships_created']} vínculo(s) criado(s), "
                f"{stats['relationships_updated']} vínculo(s) atualizado(s), "
                f"{stats['graduations_created']} graduação(ões) criada(s), "
                f"{stats['migration_cpfs']} CPF substituto(s), "
                f"{stats['financial_skipped']} financeiro não importado(s), "
                f"{stats['attendance_skipped']} histórico de aulas não importado(s)."
            )
        )

    def _load_records(self):
        data_dir = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_DIRNAME
        if not data_dir.exists():
            raise CommandError(f"Pasta não encontrada: {data_dir}")
        if not data_dir.is_dir():
            raise CommandError(f"O caminho não é uma pasta: {data_dir}")

        records = []
        for path in sorted(data_dir.glob("*.json")):
            source_code = self._extract_source_code(path)
            try:
                with path.open(encoding="utf-8") as file:
                    data = json.load(file)
            except JSONDecodeError as exc:
                raise CommandError(f"JSON inválido em {path.name}: {exc}") from exc

            if not isinstance(data, dict):
                raise CommandError(f"JSON inválido em {path.name}: objeto principal é obrigatório.")

            student_document = self._normalize_cpf(data.get("n_documento", ""))
            responsible = data.get("responsavel") or {}
            if not isinstance(responsible, dict):
                raise CommandError(f"Responsável inválido em {path.name}: objeto esperado.")

            records.append(
                {
                    "file_name": path.name,
                    "source_code": source_code,
                    "data": data,
                    "responsible": responsible,
                    "student_document": student_document,
                    "responsible_document": self._normalize_cpf(
                        responsible.get("n_documento", "")
                    ),
                }
            )
        return records

    def _extract_source_code(self, path):
        source_code = path.stem.split("-", 1)[0].strip()
        if not source_code:
            raise CommandError(f"Nome de arquivo sem código Kanri: {path.name}")
        return source_code

    def _get_person_types(self):
        required_codes = (
            PersonTypeCode.STUDENT,
            PersonTypeCode.GUARDIAN,
            PersonTypeCode.DEPENDENT,
        )
        types = {
            person_type.code: person_type
            for person_type in PersonType.objects.filter(code__in=required_codes)
        }
        missing = [code for code in required_codes if code not in types]
        if missing:
            raise CommandError(
                "Tipo(s) de pessoa ausente(s): "
                f"{', '.join(missing)}. Execute 'seed_system_initial_person_type' antes desta seed."
            )
        return types

    def _get_belt_ranks(self, records):
        required_codes = set()
        for record in records:
            birth_date = self._parse_iso_date(record["data"].get("nascimento"))
            for event in self._parse_evolution_events(record["data"], birth_date):
                required_codes.add(event["belt_code"])

        if not required_codes:
            return {}

        belt_ranks = {
            belt.code: belt
            for belt in BeltRank.objects.filter(code__in=required_codes)
        }
        missing = sorted(required_codes - set(belt_ranks))
        if missing:
            raise CommandError(
                "Faixa(s) ausente(s): "
                f"{', '.join(missing)}. Execute 'seed_system_initial_belt_ranks' antes desta seed."
            )
        return belt_ranks

    def _sync_record(
        self,
        *,
        record,
        person_types,
        student_document_counts,
        belt_ranks,
        stats,
    ):
        data = record["data"]
        warnings = []
        full_name = self._clean_text(data.get("nome", ""))
        if not full_name:
            raise CommandError(f"Nome ausente em {record['file_name']}.")

        responsible = record["responsible"]
        responsible_person = self._sync_responsible(
            responsible=responsible,
            person_types=person_types,
            stats=stats,
        )

        student_cpf = self._resolve_student_cpf(
            record=record,
            student_document_counts=student_document_counts,
            warnings=warnings,
        )
        if student_cpf.startswith(MIGRATION_CPF_PREFIX):
            stats["migration_cpfs"] += 1
        person_type = (
            person_types[PersonTypeCode.DEPENDENT]
            if responsible_person is not None and responsible_person.cpf != student_cpf
            else person_types[PersonTypeCode.STUDENT]
        )

        student_defaults, address_warnings = self._build_student_defaults(
            data=data,
            full_name=full_name,
            person_type=person_type,
        )
        warnings.extend(address_warnings)
        student, student_created = self._upsert_person(
            cpf=student_cpf,
            defaults=student_defaults,
        )
        self._count_person(stats, student_created)

        relationship_action = ""
        if responsible_person is not None and responsible_person.pk != student.pk:
            relationship, relationship_created = self._sync_relationship(
                guardian=responsible_person,
                dependent=student,
                responsible=responsible,
            )
            if relationship_created:
                stats["relationships_created"] += 1
                relationship_action = ", vínculo criado"
            else:
                stats["relationships_updated"] += 1
                relationship_action = ", vínculo atualizado"
        elif self._has_responsible_identity(responsible):
            warnings.append("responsável não vinculado porque usa a mesma pessoa do aluno")

        graduation_count = self._sync_graduations(
            person=student,
            data=data,
            belt_ranks=belt_ranks,
        )
        stats["graduations_created"] += graduation_count

        financial_count = self._list_count(data.get("financeiro"))
        attendance_count = self._list_count(data.get("historico"))
        stats["financial_skipped"] += financial_count
        stats["attendance_skipped"] += attendance_count

        action = "criado" if student_created else "atualizado"
        grad_label = f", {graduation_count} graduação(ões)" if graduation_count else ""
        financial_label = (
            f", financeiro não importado: {financial_count}"
            if financial_count
            else ""
        )
        attendance_label = (
            f", histórico de aulas não importado: {attendance_count}"
            if attendance_count
            else ""
        )
        self.stdout.write(
            f"  [{action}] {student.full_name} "
            f"(CPF {student.cpf}, tipo={student.person_type.code})"
            f"{relationship_action}{grad_label}{financial_label}{attendance_label}"
        )
        for warning in warnings:
            self.stdout.write(self.style.WARNING(f"    aviso: {record['file_name']}: {warning}"))

    def _sync_responsible(self, *, responsible, person_types, stats):
        responsible_name = self._clean_text(responsible.get("nome", ""))
        responsible_document = self._normalize_cpf(responsible.get("n_documento", ""))
        if not responsible_name and not responsible_document:
            return None
        if not responsible_name or not responsible_document:
            self.stdout.write(
                self.style.WARNING(
                    "    aviso: responsável ignorado por falta de nome ou CPF válido"
                )
            )
            return None

        defaults = {
            "full_name": responsible_name,
            "email": self._clean_text(responsible.get("email", "")),
            "phone": self._clean_text(responsible.get("telefone", "")),
            "person_type": person_types[PersonTypeCode.GUARDIAN],
            "is_active": True,
        }
        person, created = self._upsert_person(cpf=responsible_document, defaults=defaults)
        self._count_person(stats, created)
        return person

    def _resolve_student_cpf(self, *, record, student_document_counts, warnings):
        data = record["data"]
        student_document = record["student_document"]
        responsible_document = record["responsible_document"]
        document_type = data.get("tipo_documento", "")
        source_code = record["source_code"]

        uses_responsible_document = self._document_type_indicates_responsible(document_type)
        same_as_responsible = (
            bool(student_document)
            and bool(responsible_document)
            and student_document == responsible_document
            and self._names_are_different(
                data.get("nome", ""),
                record["responsible"].get("nome", ""),
            )
        )
        shared_document = bool(student_document) and student_document_counts[student_document] > 1

        if not student_document:
            warnings.append("CPF substituto usado porque o documento do aluno está ausente ou inválido")
            return self._migration_cpf(source_code)
        if uses_responsible_document:
            warnings.append(
                f"CPF substituto usado porque tipo_documento='{document_type}' indica CPF do responsável"
            )
            return self._migration_cpf(source_code)
        if same_as_responsible:
            warnings.append("CPF substituto usado porque o documento do aluno é igual ao do responsável")
            return self._migration_cpf(source_code)
        if shared_document:
            warnings.append("CPF substituto usado porque o documento aparece em mais de um aluno")
            return self._migration_cpf(source_code)
        return student_document

    def _migration_cpf(self, source_code):
        return f"{MIGRATION_CPF_PREFIX}{source_code}"

    def _build_student_defaults(self, *, data, full_name, person_type):
        birth_date = self._parse_iso_date(data.get("nascimento"))
        evolution_events = self._parse_evolution_events(data, birth_date)
        current_evolution = evolution_events[-1] if evolution_events else None
        start_event = self._get_start_event(evolution_events)
        address_defaults, address_warnings = self._build_address_defaults(data.get("endereco"))

        defaults = {
            "full_name": full_name,
            "email": self._clean_text(data.get("email", "")),
            "phone": self._clean_text(data.get("telefone", "")),
            "birth_date": birth_date,
            "biological_sex": self._map_biological_sex(data.get("sexo", "")),
            "martial_art": MartialArt.JIU_JITSU,
            "person_type": person_type,
            "is_active": True,
            "martial_art_started_at": start_event["date"] if start_event else None,
            "martial_art_last_graduation_at": (
                current_evolution["date"] if current_evolution else None
            ),
            "martial_art_graduation": current_evolution["label"] if current_evolution else "",
            "jiu_jitsu_belt": (
                PERSON_BELT_BY_RANK_CODE.get(current_evolution["belt_code"], "")
                if current_evolution
                else ""
            ),
            "jiu_jitsu_stripes": current_evolution["grade"] if current_evolution else None,
        }
        defaults.update(address_defaults)
        return defaults, address_warnings

    def _build_address_defaults(self, address):
        if not isinstance(address, dict):
            address = {}

        warnings = []
        field_map = {
            "postal_code": "cep",
            "address": "logradouro",
            "address_number": "numero",
            "address_complement": "complemento",
            "address_neighborhood": "bairro",
            "city": "cidade",
        }
        defaults = {}
        for model_field, source_field in field_map.items():
            value, removed_placeholder = self._clean_address_value(address.get(source_field, ""))
            defaults[model_field] = value
            if removed_placeholder:
                warnings.append(f"placeholder de endereço removido em {source_field}")
        return defaults, warnings

    def _sync_relationship(self, *, guardian, dependent, responsible):
        defaults = {
            "kinship_type": self._normalize_kinship(responsible.get("vinculo", "")),
            "notes": self._build_relationship_notes(responsible),
        }
        relationship, created = PersonRelationship.objects.get_or_create(
            source_person=guardian,
            target_person=dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            defaults=defaults,
        )
        if not created:
            relationship.kinship_type = defaults["kinship_type"]
            relationship.notes = defaults["notes"]
            relationship.save(update_fields=("kinship_type", "notes", "updated_at"))
        return relationship, created

    def _sync_graduations(self, *, person, data, belt_ranks):
        birth_date = self._parse_iso_date(data.get("nascimento"))
        events = self._parse_evolution_events(data, birth_date)
        if not events:
            return 0

        existing = {
            (belt_code, grade, awarded_at.isoformat())
            for belt_code, grade, awarded_at in person.graduations.values_list(
                "belt_rank__code",
                "grade_number",
                "awarded_at",
            )
        }

        created = 0
        for event in events:
            key = (
                event["belt_code"],
                event["grade"],
                event["date"].isoformat(),
            )
            if key in existing:
                continue
            Graduation.objects.create(
                person=person,
                belt_rank=belt_ranks[event["belt_code"]],
                grade_number=event["grade"],
                awarded_at=event["date"],
                notes=self._clean_text(event["type"])[:255],
            )
            existing.add(key)
            created += 1
        return created

    def _parse_evolution_events(self, data, birth_date):
        raw_events = data.get("evolucao") or []
        if not isinstance(raw_events, list):
            return []

        events = []
        for raw_event in raw_events:
            if not isinstance(raw_event, dict):
                continue
            awarded_at = self._parse_iso_date(raw_event.get("data"))
            label = self._clean_text(raw_event.get("faixa", ""))
            if not awarded_at or not label:
                continue
            belt_code = self._resolve_belt_code(label, birth_date, awarded_at)
            if not belt_code:
                self.stdout.write(
                    self.style.WARNING(
                        f"    aviso: faixa Kanri sem mapeamento ignorada: {label}"
                    )
                )
                continue
            events.append(
                {
                    "date": awarded_at,
                    "label": label,
                    "belt_code": belt_code,
                    "grade": self._parse_grade(raw_event.get("grau", "")),
                    "type": self._clean_text(raw_event.get("tipo", "")),
                }
            )
        return sorted(events, key=lambda event: event["date"])

    def _resolve_belt_code(self, label, birth_date, awarded_at):
        normalized = self._normalize_text(label)
        if "cinza" in normalized:
            return "kids-grey"
        if "amarela" in normalized:
            return "kids-yellow"
        if "laranja" in normalized:
            return "kids-orange"
        if "verde" in normalized:
            return "kids-green"
        if "azul" in normalized:
            return "adult-blue"
        if "roxa" in normalized:
            return "adult-purple"
        if "marrom" in normalized:
            return "adult-brown"
        if "preta" in normalized:
            return "adult-black"
        if "branca" in normalized:
            if "infantil" in normalized:
                return "kids-white"
            if self._is_child_at_date(birth_date, awarded_at):
                return "kids-white"
            return "adult-white"
        return ""

    def _upsert_person(self, *, cpf, defaults):
        person, created = Person.objects.get_or_create(cpf=cpf, defaults=defaults)
        if not created:
            for field, value in defaults.items():
                setattr(person, field, value)
            person.save()
        return person, created

    def _count_person(self, stats, created):
        if created:
            stats["persons_created"] += 1
        else:
            stats["persons_updated"] += 1

    def _empty_stats(self):
        return {
            "persons_created": 0,
            "persons_updated": 0,
            "relationships_created": 0,
            "relationships_updated": 0,
            "graduations_created": 0,
            "migration_cpfs": 0,
            "financial_skipped": 0,
            "attendance_skipped": 0,
        }

    def _normalize_cpf(self, value):
        value = self._clean_text(value)
        if not value:
            return ""
        try:
            return format_cpf_digits(value)
        except ValueError:
            return ""

    def _parse_iso_date(self, value):
        value = self._clean_text(value)
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _parse_grade(self, value):
        digits = only_digits(self._clean_text(value))
        if not digits:
            return 0
        return int(digits)

    def _map_biological_sex(self, value):
        normalized = self._normalize_text(value)
        if normalized == "masculino":
            return BiologicalSex.MALE
        if normalized == "feminino":
            return BiologicalSex.FEMALE
        return ""

    def _document_type_indicates_responsible(self, value):
        normalized = self._normalize_text(value)
        responsible_markers = ("pai", "mae", "avo", "vo")
        return any(marker in normalized for marker in responsible_markers)

    def _has_responsible_identity(self, responsible):
        return bool(
            self._clean_text(responsible.get("nome", ""))
            or self._normalize_cpf(responsible.get("n_documento", ""))
        )

    def _names_are_different(self, first, second):
        first_normalized = self._normalize_text(first)
        second_normalized = self._normalize_text(second)
        if not first_normalized or not second_normalized:
            return False
        return first_normalized != second_normalized

    def _get_start_event(self, events):
        if not events:
            return None
        for event in events:
            if "inicio" in self._normalize_text(event["type"]):
                return event
        return events[0]

    def _build_relationship_notes(self, responsible):
        notes = self._clean_text(responsible.get("observacoes", ""))
        if responsible.get("responsavel_financeiro") and "financeiro" not in self._normalize_text(notes):
            notes = f"{notes} Responsável financeiro no Kanri".strip()
        return notes[:255]

    def _normalize_kinship(self, value):
        normalized = self._normalize_text(value)
        if normalized in {"pai", "mae", "avo", "vo"}:
            return normalized
        return normalized[:24]

    def _is_child_at_date(self, birth_date, reference_date):
        if not birth_date:
            return False
        age = reference_date.year - birth_date.year
        has_had_birthday = (reference_date.month, reference_date.day) >= (
            birth_date.month,
            birth_date.day,
        )
        if not has_had_birthday:
            age -= 1
        return age < 16

    def _clean_address_value(self, value):
        value = self._clean_text(value)
        if self._normalize_text(value) in PLACEHOLDER_VALUES:
            return "", True
        return value, False

    def _clean_text(self, value):
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_text(self, value):
        cleaned = self._clean_text(value).lower()
        normalized = unicodedata.normalize("NFKD", cleaned)
        return "".join(character for character in normalized if not unicodedata.combining(character))

    def _list_count(self, value):
        if isinstance(value, list):
            return len(value)
        return 0
