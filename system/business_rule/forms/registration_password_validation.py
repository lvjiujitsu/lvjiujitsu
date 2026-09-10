from system.business_rule.constants import RegistrationProfile


class RegistrationPasswordMixin:
    def _clean_passwords(self, profile, include_dependent, extra_dependents):
        groups = []
        if profile == RegistrationProfile.HOLDER:
            groups.append(("holder_password", "holder_password_confirm", "aluno titular"))
            if include_dependent:
                groups.append(("dependent_password", "dependent_password_confirm", "dependente"))
        elif profile == RegistrationProfile.GUARDIAN:
            groups.append(("guardian_password", "guardian_password_confirm", "responsável"))
            groups.append(("student_password", "student_password_confirm", "dependente"))
        else:
            groups.append(("other_password", "other_password_confirm", "cadastro"))

        for password_field, confirm_field, label in groups:
            self._validate_password_pair(
                self.cleaned_data.get(password_field),
                self.cleaned_data.get(confirm_field),
                confirm_field,
                label,
            )

        for index, dependent in enumerate(extra_dependents, start=1):
            self._validate_password_pair(
                dependent.get("password"),
                dependent.get("password_confirm"),
                None,
                f"dependente adicional {index}",
            )

    def _validate_password_pair(self, password, confirm_password, error_field, label):
        if not password or not confirm_password:
            return
        if password != confirm_password:
            message = f"As senhas de {label} não coincidem."
            if error_field:
                self.add_error(error_field, message)
            else:
                self.add_error(None, message)
