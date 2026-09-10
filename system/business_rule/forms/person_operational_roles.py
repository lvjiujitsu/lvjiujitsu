from system.business_rule.constants import OperationalRoleCode


class PersonOperationalRolesMixin:
    @property
    def operational_role_fields(self):
        if not self.show_operational_role_fields:
            return []
        return self._bound_fields(self.operational_role_field_names)

    def _clean_operational_roles(self, cleaned_data):
        if not self.show_operational_role_fields:
            cleaned_data["operational_roles"] = []
            return
        selected_roles = cleaned_data.get("operational_roles") or []
        needs_class_group = any(
            role.code == OperationalRoleCode.CLASS_ASSISTANT for role in selected_roles
        )
        if needs_class_group and not cleaned_data.get("class_assistant_group"):
            self.add_error(
                "class_assistant_group",
                "Selecione a turma para o apoio de turma.",
            )
