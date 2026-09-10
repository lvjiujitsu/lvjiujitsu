from system.business_rule.constants import RegistrationProfile


class RegistrationKinshipMixin:
    def _clean_kinship(self, profile, include_dependent, extra_dependents):
        prefixes = []
        if profile == RegistrationProfile.HOLDER and include_dependent:
            prefixes.append("dependent")
        if profile == RegistrationProfile.GUARDIAN:
            prefixes.append("student")

        for prefix in prefixes:
            kinship_type = self.cleaned_data.get(f"{prefix}_kinship_type") or ""
            other_label = (self.cleaned_data.get(f"{prefix}_kinship_other_label") or "").strip()
            if kinship_type == "other" and not other_label:
                self.add_error(
                    f"{prefix}_kinship_other_label",
                    "Informe o grau de parentesco.",
                )

        for index, dependent in enumerate(extra_dependents, start=1):
            if dependent.get("kinship_type") == "other" and not (dependent.get("kinship_other_label") or "").strip():
                self.add_error(None, f"Dependente adicional {index}: informe o grau de parentesco.")
