from datetime import date
from system.business_rule.models.graduation import Graduation


class KanriGraduationMixin:
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

    def _get_start_event(self, events):
        if not events:
            return None
        for event in events:
            if "inicio" in self._normalize_text(event["type"]):
                return event
        return events[0]
