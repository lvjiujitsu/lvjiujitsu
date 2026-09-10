from system.business_rule.models.class_membership import get_class_group_eligibility_error
from system.business_rule.constants import RegistrationProfile
from system.business_rule.services.class_overview import get_public_class_group_choice_options
from system.business_rule.services.registration import resolve_class_groups


class RegistrationClassLinksMixin:
    def _configure_class_choices(self):
        group_choices = [("", "Selecione")] + get_public_class_group_choice_options()
        for prefix in ("holder", "dependent", "student"):
            self.fields[f"{prefix}_class_groups"].choices = group_choices

    def _clean_class_links(self, profile, include_dependent, extra_dependents):
        if profile == RegistrationProfile.HOLDER:
            self._resolve_class_group_collection("holder", required=self.catalog_is_available)
            if include_dependent:
                self._resolve_class_group_collection(
                    "dependent",
                    required=self.catalog_is_available,
                )
        elif profile == RegistrationProfile.GUARDIAN:
            self._resolve_class_group_collection("student", required=self.catalog_is_available)

        for index, dependent in enumerate(extra_dependents, start=1):
            if not dependent.get("biological_sex"):
                self.add_error(None, f"Dependente adicional {index}: informe o sexo biológico.")
            raw_group_ids = dependent.get("class_groups") or []
            if not self.catalog_is_available and not raw_group_ids:
                dependent["class_groups"] = []
                continue
            groups = resolve_class_groups(raw_group_ids)
            if self.catalog_is_available and not groups:
                self.add_error(None, f"Dependente adicional {index}: selecione ao menos uma turma.")
                continue
            if self._has_invalid_class_group_selection(raw_group_ids):
                self.add_error(
                    None,
                    f"Dependente adicional {index}: selecione apenas turmas válidas.",
                )
            self._add_class_group_eligibility_errors(
                None,
                groups,
                dependent.get("birth_date"),
                dependent.get("biological_sex", ""),
                f"Dependente adicional {index}",
            )
            dependent["class_groups"] = groups

    def _resolve_class_group_collection(self, prefix, required):
        field_name = f"{prefix}_class_groups"
        raw_group_ids = [
            v for v in (self.cleaned_data.get(field_name) or [])
            if v and not str(v).startswith("[")
        ]

        if not raw_group_ids and not required:
            self.cleaned_data[field_name] = []
            return

        if required and not self.catalog_is_available:
            self.cleaned_data[field_name] = []
            return

        groups = resolve_class_groups(raw_group_ids)

        if required and not groups:
            self.add_error(field_name, "Selecione ao menos uma turma.")
        if self._has_invalid_class_group_selection(raw_group_ids):
            self.add_error(field_name, "Selecione apenas turmas válidas.")

        self._add_class_group_eligibility_errors(
            field_name,
            groups,
            self.cleaned_data.get(f"{prefix}_birthdate"),
            self.cleaned_data.get(f"{prefix}_biological_sex", ""),
        )
        self.cleaned_data[field_name] = groups

    def _has_invalid_class_group_selection(self, raw_group_ids):
        for raw_group_id in raw_group_ids:
            if not str(raw_group_id):
                continue
            if resolve_class_groups([raw_group_id]):
                continue
            return True
        return False

    def _add_class_group_eligibility_errors(
        self,
        field_name,
        class_groups,
        birth_date,
        biological_sex,
        label_prefix=None,
    ):
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=birth_date,
                biological_sex=biological_sex,
                class_group=class_group,
            )
            if not error:
                continue
            message = f"{class_group.class_category.display_name} · {class_group.display_name}: {error}"
            if label_prefix:
                self.add_error(None, f"{label_prefix}: {message}")
            else:
                self.add_error(field_name, message)
