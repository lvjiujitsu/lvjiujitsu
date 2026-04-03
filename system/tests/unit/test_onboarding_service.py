import pytest
from datetime import date
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from system.models import StudentProfile
from system.services.onboarding.workflow import submit_household_onboarding
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_onboarding_service_rolls_back_when_dependent_conflicts():
    existing_student = StudentProfileFactory()
    factory = RequestFactory()
    request = factory.post("/onboarding/confirmacao/")
    holder_data = {
        "holder_full_name": "Titular Teste",
        "holder_cpf": "11122233344",
        "holder_email": "titular@example.com",
        "holder_birth_date": date(1990, 1, 1),
        "holder_contact_phone": "11988887777",
        "holder_timezone": "America/Sao_Paulo",
        "responsible_same_as_holder": True,
        "emergency_contact_name": "Mae",
        "emergency_contact_phone": "11999990000",
        "emergency_contact_relationship": "Mae",
    }
    dependents_data = [
        {
            "full_name": "Dependente Duplicado",
            "cpf": existing_student.user.cpf,
            "birth_date": date(2012, 1, 1),
            "relationship_type": "guardian",
            "has_own_credential": False,
        }
    ]

    with pytest.raises(ValidationError):
        submit_household_onboarding(
            holder_data=holder_data,
            dependents_data=dependents_data,
            accepted_term_ids=[],
            request=request,
        )

    assert StudentProfile.objects.filter(user__cpf="11122233344").exists() is False
