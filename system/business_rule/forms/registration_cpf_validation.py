from system.business_rule.models import Person
from system.core.documents import ensure_formatted_cpf


class RegistrationCpfMixin:
    def _clean_cpfs(self, extra_dependents):
        seen_cpfs = set()
        for field_name in (
            "holder_cpf",
            "dependent_cpf",
            "guardian_cpf",
            "student_cpf",
            "other_cpf",
        ):
            value = self.cleaned_data.get(field_name)
            if not value:
                continue
            self.cleaned_data[field_name] = self._validate_single_cpf(value, field_name, seen_cpfs)

        for index, dependent in enumerate(extra_dependents, start=1):
            value = dependent.get("cpf")
            if not value:
                continue
            dependent["cpf"] = self._validate_single_cpf(value, None, seen_cpfs, index=index)

    def _validate_single_cpf(self, value, field_name, seen_cpfs, index=None):
        try:
            formatted = ensure_formatted_cpf(value)
        except ValueError as error:
            if field_name:
                self.add_error(field_name, str(error))
            else:
                self.add_error(None, f"Dependente adicional {index}: {error}")
            return value

        if formatted in seen_cpfs:
            message = "CPF duplicado no cadastro."
            if field_name:
                self.add_error(field_name, message)
            else:
                self.add_error(None, f"Dependente adicional {index}: {message}")
            return value

        existing = Person.objects.filter(cpf=formatted).first()
        if existing is not None and existing.is_active:
            message = "CPF já cadastrado no sistema."
            if field_name:
                self.add_error(field_name, message)
            else:
                self.add_error(None, f"Dependente adicional {index}: {message}")
            return value

        seen_cpfs.add(formatted)
        return formatted
