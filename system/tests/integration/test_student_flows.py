import pytest
from django.urls import reverse

from system.models import ConsentAcceptance, LgpdRequest, SensitiveAccessLog, StudentProfile
from system.services.lgpd.records import build_term_field_name, get_required_onboarding_terms
from system.tests.factories.auth_factories import AdminUserFactory, SystemUserFactory
from system.tests.factories.student_factories import ConsentTermFactory, EmergencyRecordFactory, StudentProfileFactory


@pytest.mark.django_db
def test_onboarding_wizard_creates_holder_dependent_and_terms(client):
    term = ConsentTermFactory(code="privacy_policy", version=3)
    confirm_payload = {"confirm_data_accuracy": "on"}
    for required_term in get_required_onboarding_terms():
        confirm_payload[build_term_field_name(required_term)] = "on"

    holder_response = client.post(
        reverse("system:onboarding-holder"),
        data={
            "holder_full_name": "Titular Publico",
            "holder_cpf": "11122233344",
            "holder_email": "titular@teste.com",
            "holder_birth_date": "1990-01-01",
            "holder_contact_phone": "11999998888",
            "holder_timezone": "America/Sao_Paulo",
            "responsible_same_as_holder": "on",
            "emergency_contact_name": "Contato Mae",
            "emergency_contact_phone": "11999990000",
            "emergency_contact_relationship": "Mae",
        },
    )
    dependent_response = client.post(
        reverse("system:onboarding-dependents"),
        data={
            "dependents-TOTAL_FORMS": "2",
            "dependents-INITIAL_FORMS": "0",
            "dependents-MIN_NUM_FORMS": "0",
            "dependents-MAX_NUM_FORMS": "1000",
            "dependents-0-full_name": "Dependente Teste",
            "dependents-0-cpf": "55566677788",
            "dependents-0-birth_date": "2010-02-02",
            "dependents-0-relationship_type": "guardian",
            "dependents-0-has_own_credential": "",
            "dependents-0-contact_phone": "",
            "dependents-1-full_name": "",
            "dependents-1-cpf": "",
            "dependents-1-birth_date": "",
            "dependents-1-relationship_type": "",
        },
    )
    confirm_response = client.post(
        reverse("system:onboarding-confirm"),
        data=confirm_payload,
    )

    holder_profile = StudentProfile.objects.get(user__cpf="11122233344")
    dependent_profile = StudentProfile.objects.get(user__cpf="55566677788")

    assert holder_response.status_code == 302
    assert dependent_response.status_code == 302
    assert confirm_response.status_code == 302
    assert holder_profile.student_type == StudentProfile.TYPE_HOLDER
    assert dependent_profile.student_type == StudentProfile.TYPE_DEPENDENT
    assert ConsentAcceptance.objects.filter(user=holder_profile.user, term=term).exists() is True


@pytest.mark.django_db
def test_onboarding_formset_rejects_duplicate_dependent_cpf(client):
    client.post(
        reverse("system:onboarding-holder"),
        data={
            "holder_full_name": "Titular Publico",
            "holder_cpf": "11122233344",
            "holder_birth_date": "1990-01-01",
            "holder_timezone": "America/Sao_Paulo",
            "responsible_same_as_holder": "on",
        },
    )

    response = client.post(
        reverse("system:onboarding-dependents"),
        data={
            "dependents-TOTAL_FORMS": "2",
            "dependents-INITIAL_FORMS": "0",
            "dependents-MIN_NUM_FORMS": "0",
            "dependents-MAX_NUM_FORMS": "1000",
            "dependents-0-full_name": "Dependente Um",
            "dependents-0-cpf": "55566677788",
            "dependents-0-birth_date": "2011-01-01",
            "dependents-0-relationship_type": "guardian",
            "dependents-1-full_name": "Dependente Dois",
            "dependents-1-cpf": "55566677788",
            "dependents-1-birth_date": "2012-01-01",
            "dependents-1-relationship_type": "guardian",
        },
    )

    assert response.status_code == 200
    assert "Nao repita o mesmo CPF entre dependentes." in response.content.decode()


@pytest.mark.django_db
def test_my_profile_updates_name_without_changing_cpf(client):
    user = SystemUserFactory(password="StrongPassword123")
    client.force_login(user)

    response = client.post(
        reverse("system:my-profile"),
        data={
            "action": "profile",
            "profile-full_name": "Nome Atualizado",
            "profile-email": "novo@example.com",
            "profile-timezone": "America/Sao_Paulo",
            "cpf": "99999999999",
        },
    )

    user.refresh_from_db()

    assert response.status_code == 302
    assert user.full_name == "Nome Atualizado"
    assert user.cpf != "99999999999"


@pytest.mark.django_db
def test_my_profile_changes_password_and_creates_lgpd_request(client):
    user = SystemUserFactory(password="StrongPassword123")
    client.force_login(user)

    password_response = client.post(
        reverse("system:my-profile"),
        data={
            "action": "password",
            "password-current_password": "StrongPassword123",
            "password-new_password": "NewPassword123",
            "password-new_password_confirmation": "NewPassword123",
        },
    )
    lgpd_response = client.post(
        reverse("system:my-profile"),
        data={
            "action": "lgpd",
            "lgpd-request_type": LgpdRequest.TYPE_ACCESS,
            "lgpd-notes": "Quero meu relatorio de dados.",
        },
    )

    user.refresh_from_db()

    assert password_response.status_code == 302
    assert lgpd_response.status_code == 302
    assert user.check_password("NewPassword123") is True
    assert LgpdRequest.objects.filter(user=user, request_type=LgpdRequest.TYPE_ACCESS).exists() is True


@pytest.mark.django_db
def test_admin_student_list_filters_by_status(client):
    admin = AdminUserFactory()
    StudentProfileFactory(operational_status=StudentProfile.STATUS_ACTIVE)
    StudentProfileFactory(operational_status=StudentProfile.STATUS_INACTIVE)
    client.force_login(admin)

    response = client.get(reverse("system:student-list"), data={"status": StudentProfile.STATUS_ACTIVE})

    assert response.status_code == 200
    assert "Ativo" in response.content.decode()


@pytest.mark.django_db
def test_student_update_requires_admin_and_logs_sensitive_access(client):
    student = StudentProfileFactory()
    EmergencyRecordFactory(student=student)
    regular_user = SystemUserFactory(password="StrongPassword123")
    client.force_login(regular_user)

    denied_response = client.get(reverse("system:student-update", kwargs={"uuid": student.uuid}))

    admin = AdminUserFactory()
    client.force_login(admin)
    allowed_response = client.get(reverse("system:student-update", kwargs={"uuid": student.uuid}))

    assert denied_response.status_code == 403
    assert allowed_response.status_code == 200
    assert SensitiveAccessLog.objects.filter(student=student, access_type=SensitiveAccessLog.ACCESS_EMERGENCY_VIEW).exists()


@pytest.mark.django_db
def test_profile_page_displays_consent_history(client):
    user = SystemUserFactory(password="StrongPassword123")
    term = ConsentTermFactory(code="service_agreement", version=2)
    ConsentAcceptance.objects.create(user=user, term=term, context="profile")
    client.force_login(user)

    response = client.get(reverse("system:my-profile"))

    assert response.status_code == 200
    assert "Termo" in response.content.decode()
