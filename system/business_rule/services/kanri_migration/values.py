import unicodedata
from datetime import date
from system.business_rule.models import BiologicalSex
from system.core.documents import format_cpf_digits, only_digits
from system.business_rule.services.kanri_migration.constants import (
    MIGRATION_CPF_PREFIX,
    PLACEHOLDER_VALUES,
)


class KanriValueMixin:
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

    def _migration_cpf(self, source_code):
        return f"{MIGRATION_CPF_PREFIX}{source_code}"
