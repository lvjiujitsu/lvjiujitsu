from django import forms
from system.business_rule.models import (
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PreRegistration,
    PreRegistrationStatus,
)
from system.core.documents import ensure_formatted_cpf
from system.business_rule.forms.dependent_form_helpers import DEPENDENT_FLOW_KIND


class DependentCpfMixin:
    def clean_dependent_cpf(self):
        value = self.cleaned_data.get("dependent_cpf")
        try:
            formatted = ensure_formatted_cpf(value)
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error
        active_person = Person.objects.filter(cpf=formatted, is_active=True).first()
        if active_person is not None:
            if self._is_owned_dependent(active_person):
                self.existing_owned_dependent = active_person
                return formatted
            raise forms.ValidationError("Já existe uma pessoa ativa com este CPF.")
        if self._has_pending_pre_registration_for_cpf(formatted):
            raise forms.ValidationError(
                "Já existe um pré-cadastro pendente para este CPF."
            )
        return formatted

    def _is_owned_dependent(self, person):
        if self.owner is None:
            return False
        return PersonRelationship.objects.filter(
            source_person=self.owner,
            target_person=person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        ).exists()

    def _has_pending_pre_registration_for_cpf(self, cpf):
        if self.owner is None:
            return False
        queryset = PreRegistration.objects.filter(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            status__in=(
                PreRegistrationStatus.DRAFT,
                PreRegistrationStatus.AWAITING_PAYMENT,
                PreRegistrationStatus.PAYMENT_CONFIRMED,
            ),
        )
        if self.pending is not None:
            queryset = queryset.exclude(pk=self.pending.pk)
        for pre_registration in queryset.only("pk", "form_snapshot"):
            snapshot = pre_registration.form_snapshot or {}
            if snapshot.get("flow_kind") != DEPENDENT_FLOW_KIND:
                continue
            if snapshot.get("owner_person_id") != self.owner.pk:
                continue
            if snapshot.get("dependent_cpf") == cpf:
                return True
        return False
