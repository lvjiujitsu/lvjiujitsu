from system.business_rule.models import PersonType
from system.business_rule.constants import RegistrationProfile, STUDENT_PORTAL_PERSON_TYPE_CODES


class RegistrationPersonTypeMixin:
    def _configure_other_type_choices(self):
        choices = [("", "Selecione")]
        queryset = PersonType.objects.filter(is_active=True).exclude(
            code__in=STUDENT_PORTAL_PERSON_TYPE_CODES
        )
        choices.extend((item.code, item.display_name) for item in queryset.order_by("display_name"))
        self.fields["other_type_code"].choices = choices

    def _clean_other_type_code(self, profile):
        selected_code = self.cleaned_data.get("other_type_code") or ""
        available_codes = {code for code, _label in self.fields["other_type_code"].choices if code}
        if profile != RegistrationProfile.OTHER:
            self.cleaned_data["other_type_code"] = ""
            return
        if not available_codes:
            self.add_error(
                "other_type_code",
                "Nenhum tipo adicional está disponível para esse cadastro.",
            )
            return
        if available_codes and selected_code not in available_codes:
            self.add_error("other_type_code", "Selecione um tipo de cadastro válido.")
        if available_codes and not selected_code:
            self.add_error("other_type_code", "Selecione um tipo de cadastro.")
