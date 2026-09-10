from system.business_rule.models.class_membership import get_class_group_eligibility_error
from system.business_rule.services.registration import resolve_class_groups


class DependentClassesMixin:
    def _clean_classes(self, cleaned_data):
        values = cleaned_data.get("dependent_class_groups") or []
        class_groups = resolve_class_groups(values)
        if not class_groups:
            self.add_error("dependent_class_groups", "Selecione pelo menos uma turma.")
            cleaned_data["resolved_class_groups"] = []
            return
        for class_group in class_groups:
            error = get_class_group_eligibility_error(
                birth_date=cleaned_data.get("dependent_birthdate"),
                biological_sex=cleaned_data.get("dependent_biological_sex") or "",
                class_group=class_group,
            )
            if error:
                self.add_error("dependent_class_groups", error)
                break
        cleaned_data["resolved_class_groups"] = class_groups
