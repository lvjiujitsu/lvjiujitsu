from system.business_rule.forms.registration_common import MARTIAL_ART_EXPERIENCE_YES
from system.business_rule.models import MartialArt


class DependentMartialArtMixin:
    def _clean_martial_art(self, cleaned_data):
        has_martial_art = cleaned_data.get("dependent_has_martial_art") or ""
        martial_art = cleaned_data.get("dependent_martial_art") or ""
        if martial_art and not has_martial_art:
            has_martial_art = MARTIAL_ART_EXPERIENCE_YES
        cleaned_data["dependent_has_martial_art"] = has_martial_art
        if has_martial_art != MARTIAL_ART_EXPERIENCE_YES:
            cleaned_data["dependent_martial_art"] = ""
            cleaned_data["dependent_martial_art_graduation"] = ""
            cleaned_data["dependent_jiu_jitsu_belt"] = ""
            cleaned_data["dependent_jiu_jitsu_stripes"] = None
            return
        if not martial_art:
            self.add_error("dependent_martial_art", "Informe a arte marcial.")
            return
        if martial_art == MartialArt.JIU_JITSU:
            if not cleaned_data.get("dependent_jiu_jitsu_belt"):
                self.add_error(
                    "dependent_jiu_jitsu_belt",
                    "Informe a faixa de Jiu Jitsu.",
                )
            cleaned_data["dependent_martial_art_graduation"] = ""
        elif not cleaned_data.get("dependent_martial_art_graduation"):
            self.add_error(
                "dependent_martial_art_graduation",
                "Informe a graduação atual.",
            )
            cleaned_data["dependent_jiu_jitsu_belt"] = ""
            cleaned_data["dependent_jiu_jitsu_stripes"] = None
