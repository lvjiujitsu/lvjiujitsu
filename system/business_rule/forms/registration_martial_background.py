from system.business_rule.models import MartialArt
from system.business_rule.constants import RegistrationProfile
from system.business_rule.forms.registration_common import MARTIAL_ART_EXPERIENCE_YES


class RegistrationMartialBackgroundMixin:
    def _clean_martial_background(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == RegistrationProfile.HOLDER:
            prefixes.append("holder")
            if include_dependent:
                prefixes.append("dependent")
        elif profile == RegistrationProfile.GUARDIAN:
            prefixes.append("guardian")
            prefixes.append("student")
        elif profile == RegistrationProfile.OTHER:
            prefixes.append("other")

        for prefix in prefixes:
            has_martial_art = self._normalize_martial_art_answer(
                self.cleaned_data.get(f"{prefix}_has_martial_art") or "",
                self.cleaned_data.get(f"{prefix}_martial_art") or "",
            )
            self.cleaned_data[f"{prefix}_has_martial_art"] = has_martial_art
            martial_art = self.cleaned_data.get(f"{prefix}_martial_art") or ""
            graduation = (self.cleaned_data.get(f"{prefix}_martial_art_graduation") or "").strip()
            belt = self.cleaned_data.get(f"{prefix}_jiu_jitsu_belt") or ""
            if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
                self._clear_martial_background_fields(prefix)
                continue
            if not martial_art:
                self.add_error(
                    f"{prefix}_martial_art",
                    "Selecione a arte marcial praticada.",
                )
                self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None
                continue
            if martial_art != MartialArt.JIU_JITSU and not graduation:
                self.add_error(
                    f"{prefix}_martial_art_graduation",
                    "Informe a graduação/nível na arte marcial.",
                )
            if martial_art == MartialArt.JIU_JITSU and not belt:
                self.add_error(
                    f"{prefix}_jiu_jitsu_belt",
                    "Informe a faixa de Jiu Jitsu.",
                )
            if martial_art != MartialArt.JIU_JITSU:
                self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
                self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None
            if not martial_art or martial_art == MartialArt.JIU_JITSU:
                self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""

        for index, dependent in enumerate(extra_dependents, start=1):
            has_martial_art = self._normalize_martial_art_answer(
                dependent.get("has_martial_art") or "",
                dependent.get("martial_art") or "",
            )
            dependent["has_martial_art"] = has_martial_art
            martial_art = dependent.get("martial_art") or ""
            graduation = (dependent.get("martial_art_graduation") or "").strip()
            belt = dependent.get("jiu_jitsu_belt") or ""
            if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
                self._clear_extra_dependent_martial_background(dependent)
                continue
            if not martial_art:
                self.add_error(
                    None,
                    f"Dependente adicional {index}: selecione a arte marcial praticada.",
                )
                dependent["martial_art_graduation"] = ""
                dependent["jiu_jitsu_belt"] = ""
                dependent["jiu_jitsu_stripes"] = None
                continue
            if martial_art != MartialArt.JIU_JITSU and not graduation:
                self.add_error(None, f"Dependente adicional {index}: informe a graduação na arte marcial.")
            if martial_art == MartialArt.JIU_JITSU and not belt:
                self.add_error(None, f"Dependente adicional {index}: informe a faixa de Jiu Jitsu.")
            if martial_art != MartialArt.JIU_JITSU:
                dependent["jiu_jitsu_belt"] = ""
                dependent["jiu_jitsu_stripes"] = None
            if not martial_art or martial_art == MartialArt.JIU_JITSU:
                dependent["martial_art_graduation"] = ""

    def _normalize_martial_art_answer(self, answer, martial_art):
        if answer:
            return answer
        return MARTIAL_ART_EXPERIENCE_YES if martial_art else ""

    def _clear_martial_background_fields(self, prefix):
        self.cleaned_data[f"{prefix}_martial_art"] = ""
        self.cleaned_data[f"{prefix}_martial_art_graduation"] = ""
        self.cleaned_data[f"{prefix}_jiu_jitsu_belt"] = ""
        self.cleaned_data[f"{prefix}_jiu_jitsu_stripes"] = None

    def _clear_extra_dependent_martial_background(self, dependent):
        dependent["martial_art"] = ""
        dependent["martial_art_graduation"] = ""
        dependent["jiu_jitsu_belt"] = ""
        dependent["jiu_jitsu_stripes"] = None
