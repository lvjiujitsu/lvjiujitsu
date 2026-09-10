import json
from json import JSONDecodeError
from pathlib import Path
from django.conf import settings
from django.core.management.base import CommandError
from system.business_rule.constants import PersonTypeCode
from system.business_rule.models import PersonType
from system.business_rule.models.graduation import BeltRank
from system.business_rule.services.kanri_migration.constants import DATA_DIRNAME


class KanriSourceMixin:
    def _load_records(self):
        data_dir = Path(settings.BASE_DIR) / "static" / "business_rule" / "initial_data" / DATA_DIRNAME
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
