from datetime import datetime
from system.business_rule.services.registration import parse_extra_dependents_payload


class RegistrationExtraDependentsMixin:
    def _clean_extra_dependents_payload(self):
        payload = parse_extra_dependents_payload(self.cleaned_data.get("extra_dependents_payload"))
        cleaned_dependents = []
        for index, dependent in enumerate(payload, start=1):
            birth_date_raw = dependent.get("birth_date") or ""
            birth_date = None
            jiu_jitsu_stripes = dependent.get("jiu_jitsu_stripes")
            if jiu_jitsu_stripes in ("", None):
                jiu_jitsu_stripes = None
            else:
                try:
                    jiu_jitsu_stripes = int(jiu_jitsu_stripes)
                except (TypeError, ValueError):
                    self.add_error(None, f"Dependente adicional {index}: graus de Jiu Jitsu inválidos.")
                    jiu_jitsu_stripes = None
                if jiu_jitsu_stripes is not None and not (0 <= jiu_jitsu_stripes <= 4):
                    self.add_error(None, f"Dependente adicional {index}: graus de Jiu Jitsu deve ser entre 0 e 4.")
                    jiu_jitsu_stripes = None
            if birth_date_raw:
                try:
                    birth_date = datetime.strptime(birth_date_raw, "%d/%m/%Y").date()
                except ValueError:
                    self.add_error(
                        None,
                        f"Dependente adicional {index}: data de nascimento inválida.",
                    )
            cleaned_dependents.append(
                {
                    "full_name": (dependent.get("full_name") or "").strip(),
                    "cpf": (dependent.get("cpf") or "").strip(),
                    "birth_date": birth_date,
                    "biological_sex": dependent.get("biological_sex") or "",
                    "email": (dependent.get("email") or "").strip(),
                    "phone": (dependent.get("phone") or "").strip(),
                    "password": dependent.get("password") or "",
                    "password_confirm": dependent.get("password_confirm") or "",
                    "kinship_type": dependent.get("kinship_type") or "",
                    "kinship_other_label": (dependent.get("kinship_other_label") or "").strip(),
                    "class_groups": dependent.get("class_groups") or [],
                    "blood_type": dependent.get("blood_type") or "",
                    "allergies": dependent.get("allergies") or "",
                    "previous_injuries": dependent.get("injuries") or dependent.get("previous_injuries") or "",
                    "emergency_contact": dependent.get("emergency_contact") or "",
                    "has_martial_art": self._normalize_martial_art_answer(
                        dependent.get("has_martial_art") or "",
                        dependent.get("martial_art") or "",
                    ),
                    "martial_art": dependent.get("martial_art") or "",
                    "martial_art_graduation": dependent.get("martial_art_graduation") or "",
                    "jiu_jitsu_belt": dependent.get("jiu_jitsu_belt") or "",
                    "jiu_jitsu_stripes": jiu_jitsu_stripes,
                }
            )
        return cleaned_dependents
