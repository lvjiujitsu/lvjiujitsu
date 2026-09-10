from system.business_rule.models import PersonRelationship, PersonRelationshipKind


class KanriRelationshipMixin:
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
