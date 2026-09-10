from system.business_rule.constants import RegistrationProfile


class RegistrationRequiredFieldsMixin:
    def _clean_required_fields(self, profile, include_dependent):
        if profile == RegistrationProfile.HOLDER:
            self._require_fields(
                "holder_name",
                "holder_cpf",
                "holder_birthdate",
                "holder_biological_sex",
                "holder_password",
                "holder_password_confirm",
            )
            if include_dependent:
                self._require_fields(
                    "dependent_name",
                    "dependent_cpf",
                    "dependent_birthdate",
                    "dependent_biological_sex",
                    "dependent_password",
                    "dependent_password_confirm",
                    "dependent_kinship_type",
                )
            return

        if profile == RegistrationProfile.GUARDIAN:
            self._require_fields(
                "guardian_name",
                "guardian_cpf",
                "guardian_password",
                "guardian_password_confirm",
                "student_name",
                "student_cpf",
                "student_birthdate",
                "student_biological_sex",
                "student_password",
                "student_password_confirm",
                "student_kinship_type",
            )
            return

        self._require_fields(
            "other_name",
            "other_cpf",
            "other_birthdate",
            "other_biological_sex",
            "other_password",
            "other_password_confirm",
        )

    def _require_fields(self, *field_names):
        for field_name in field_names:
            value = self.cleaned_data.get(field_name)
            if value in (None, ""):
                self.add_error(field_name, "Campo obrigatório.")
