import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone

from system.models import AcademyConfiguration, Lead, PublicClassSchedule, PublicPlan, TrialClassRequest


@pytest.mark.django_db
def test_landing_page_renders_active_plans_and_schedules(client):
    configuration = AcademyConfiguration.objects.get()
    configuration.public_whatsapp = "(11) 99999-9999"
    configuration.save()
    PublicPlan.objects.create(
        name="Plano Mensal",
        summary="Treine 3x por semana.",
        amount="249.90",
        is_active=True,
    )
    PublicClassSchedule.objects.create(
        class_level="Fundamentos",
        weekday=PublicClassSchedule.WEEKDAY_MONDAY,
        start_time="19:00",
        end_time="20:00",
        instructor_name="Professor Lucas",
        is_active=True,
    )

    response = client.get(reverse("system:home"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Plano Mensal" in content
    assert "Fundamentos" in content
    assert "Agendar aula experimental" in content


@pytest.mark.django_db
def test_lead_capture_saves_source_and_requested_plan(client):
    plan = PublicPlan.objects.create(
        name="Plano Mensal",
        summary="Treine 3x por semana.",
        amount="249.90",
        is_active=True,
    )

    response = client.post(
        reverse("system:lead-capture"),
        data={
            "full_name": "Lead Publico",
            "email": "lead@example.com",
            "phone": "",
            "source": Lead.SOURCE_INSTAGRAM,
            "requested_plan": plan.id,
            "interest_note": "Quero treinar a noite.",
        },
    )

    lead = Lead.objects.get(email="lead@example.com")

    assert response.status_code == 302
    assert lead.source == Lead.SOURCE_INSTAGRAM
    assert lead.requested_plan == plan


@pytest.mark.django_db
def test_trial_class_request_creates_lead_and_request(client):
    response = client.post(
        reverse("system:trial-class-request"),
        data={
            "full_name": "Teste Aula",
            "email": "trial@example.com",
            "phone": "11988887777",
            "source": Lead.SOURCE_LANDING,
            "preferred_date": timezone.localdate() + timedelta(days=1),
            "preferred_period": TrialClassRequest.PERIOD_EVENING,
            "notes": "Posso chegar 15 minutos antes.",
        },
    )

    trial_request = TrialClassRequest.objects.select_related("lead").get()

    assert response.status_code == 302
    assert trial_request.lead.email == "trial@example.com"
    assert trial_request.status == TrialClassRequest.STATUS_REQUESTED
