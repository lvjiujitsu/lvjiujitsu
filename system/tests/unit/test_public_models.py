import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from system.models import AcademyConfiguration, Lead, TrialClassRequest


@pytest.mark.django_db
def test_academy_configuration_is_singleton():
    assert AcademyConfiguration.objects.count() == 1

    with pytest.raises(ValidationError):
        AcademyConfiguration.objects.create(academy_name="Outra Academia")


@pytest.mark.django_db
def test_lead_requires_email_or_phone():
    lead = Lead(full_name="Lead sem contato", source=Lead.SOURCE_LANDING)

    with pytest.raises(ValidationError):
        lead.full_clean()


@pytest.mark.django_db
def test_trial_class_request_requires_today_or_future():
    lead = Lead.objects.create(full_name="Lead", email="lead@example.com", source=Lead.SOURCE_LANDING)
    trial_request = TrialClassRequest(
        lead=lead,
        preferred_date=timezone.localdate() - timedelta(days=1),
        preferred_period=TrialClassRequest.PERIOD_EVENING,
    )

    with pytest.raises(ValidationError):
        trial_request.full_clean()
