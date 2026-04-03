from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from system.constants import ROLE_ALUNO_DEPENDENTE_COM_CREDENCIAL
from system.models import Lead, MonthlyInvoice, SystemRole, TrialClassRequest
from system.services.finance.contracts import sync_subscription_status
from system.tests.factories.auth_factories import AdminUserFactory, SystemUserFactory
from system.tests.factories.finance_factories import LocalSubscriptionFactory, MonthlyInvoiceFactory, PaymentProofFactory, SubscriptionStudentFactory
from system.tests.factories.finance_factories import EnrollmentPauseFactory
from system.tests.factories.student_factories import GuardianRelationshipFactory, StudentProfileFactory
from system.tests.factories.class_factories import ClassSessionFactory


def _build_open_self_service_session():
    return ClassSessionFactory(
        status=ClassSessionFactory._meta.model.STATUS_OPEN,
        starts_at=timezone.now() - timedelta(minutes=10),
        ends_at=timezone.now() + timedelta(minutes=40),
        class_group__reservation_required=False,
    )


def _midday(local_date):
    return timezone.make_aware(datetime.combine(local_date, datetime.min.time())) + timedelta(hours=12)


@pytest.mark.django_db
def test_portal_dashboard_redirects_admin_and_student_users(client):
    admin_user = AdminUserFactory(password="StrongPassword123")
    student_user = SystemUserFactory(password="StrongPassword123")
    StudentProfileFactory(user=student_user)

    client.force_login(admin_user)
    admin_response = client.get(reverse("system:portal-dashboard"))

    client.force_login(student_user)
    student_response = client.get(reverse("system:portal-dashboard"))

    assert admin_response.status_code == 302
    assert admin_response.url == reverse("system:admin-dashboard")
    assert student_response.status_code == 302
    assert student_response.url == reverse("system:student-dashboard")


@pytest.mark.django_db
def test_student_dashboard_shows_regularization_cta_and_precheck_widget(client):
    user = SystemUserFactory(password="StrongPassword123")
    student = StudentProfileFactory(user=user)
    subscription = LocalSubscriptionFactory(
        responsible_user=user,
        status=LocalSubscriptionFactory._meta.model.STATUS_PENDING_FINANCIAL,
    )
    SubscriptionStudentFactory(subscription=subscription, student=student)
    MonthlyInvoiceFactory(subscription=subscription, status=MonthlyInvoice.STATUS_OVERDUE, amount_net=Decimal("250.00"))
    _build_open_self_service_session()
    client.force_login(user)

    response = client.get(reverse("system:student-dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Existe pendencia financeira" in content
    assert "Ir para minhas faturas" in content
    assert "Validar acesso e testar camera" in content
    assert student.user.full_name in content


@pytest.mark.django_db
def test_student_dashboard_allows_active_precheck_before_camera(client):
    user = SystemUserFactory(password="StrongPassword123")
    StudentProfileFactory(user=user, operational_status="ACTIVE")
    session = _build_open_self_service_session()
    client.force_login(user)

    response = client.get(reverse("system:student-dashboard"))
    precheck = client.get(reverse("system:attendance-precheck", kwargs={"uuid": session.uuid}))

    assert response.status_code == 200
    assert "Validar acesso e testar camera" in response.content.decode()
    assert precheck.json()["allowed"] is True


@pytest.mark.django_db
def test_student_dashboard_blocks_pending_financial_precheck_before_camera(client):
    user = SystemUserFactory(password="StrongPassword123")
    student = StudentProfileFactory(user=user)
    subscription = LocalSubscriptionFactory(responsible_user=user)
    SubscriptionStudentFactory(subscription=subscription, student=student)
    MonthlyInvoiceFactory(subscription=subscription, status=MonthlyInvoice.STATUS_OVERDUE)
    sync_subscription_status(subscription)
    session = _build_open_self_service_session()
    client.force_login(user)

    response = client.get(reverse("system:student-dashboard"))
    precheck = client.get(reverse("system:attendance-precheck", kwargs={"uuid": session.uuid}))

    assert response.status_code == 200
    assert precheck.json()["allowed"] is False
    assert precheck.json()["reason"] == "pending_financial"


@pytest.mark.django_db
def test_student_dashboard_blocks_paused_precheck_before_camera(client):
    user = SystemUserFactory(password="StrongPassword123")
    student = StudentProfileFactory(user=user)
    EnrollmentPauseFactory(student=student, subscription=None)
    session = _build_open_self_service_session()
    client.force_login(user)

    response = client.get(reverse("system:student-dashboard"))
    precheck = client.get(reverse("system:attendance-precheck", kwargs={"uuid": session.uuid}))

    assert response.status_code == 200
    assert precheck.json()["allowed"] is False
    assert precheck.json()["reason"] == "paused"


@pytest.mark.django_db
def test_dependent_dashboard_hides_family_finance(client):
    holder_user = SystemUserFactory(password="StrongPassword123")
    dependent_user = SystemUserFactory(password="StrongPassword123")
    dependent_role, _ = SystemRole.objects.get_or_create(
        code=ROLE_ALUNO_DEPENDENTE_COM_CREDENCIAL,
        defaults={"name": "Dependente com credencial"},
    )
    dependent_user.assign_role(dependent_role)
    holder_student = StudentProfileFactory(user=holder_user)
    dependent_student = StudentProfileFactory(user=dependent_user, student_type="dependent")
    GuardianRelationshipFactory(student=dependent_student, responsible_user=holder_user)
    subscription = LocalSubscriptionFactory(responsible_user=holder_user)
    SubscriptionStudentFactory(subscription=subscription, student=holder_student)
    SubscriptionStudentFactory(subscription=subscription, student=dependent_student, is_primary_student=False)
    MonthlyInvoiceFactory(subscription=subscription, amount_net=Decimal("310.00"))
    client.force_login(dependent_user)

    response = client.get(reverse("system:student-dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "nao exibe financeiro familiar" in content
    assert "310.00" not in content
    assert dependent_student.user.full_name in content


@pytest.mark.django_db
def test_student_dashboard_switches_household_context_between_visible_students(client):
    holder_user = SystemUserFactory(password="StrongPassword123")
    holder_student = StudentProfileFactory(user=holder_user)
    dependent_student = StudentProfileFactory(student_type="dependent")
    GuardianRelationshipFactory(student=dependent_student, responsible_user=holder_user)
    client.force_login(holder_user)

    response = client.get(reverse("system:student-dashboard"), {"student_uuid": str(dependent_student.uuid)})

    assert response.status_code == 200
    assert response.context["selected_student"] == dependent_student
    assert holder_student in response.context["visible_students"]
    assert dependent_student in response.context["visible_students"]


@pytest.mark.django_db
def test_admin_dashboard_renders_snapshot_and_pending_operational_lists(client):
    admin_user = AdminUserFactory(password="StrongPassword123")
    overdue_invoice = MonthlyInvoiceFactory(status=MonthlyInvoice.STATUS_OVERDUE)
    PaymentProofFactory(status="UNDER_REVIEW")
    lead = Lead.objects.create(full_name="Lead Dashboard", phone="11999990000")
    TrialClassRequest.objects.create(
        lead=lead,
        preferred_date=timezone.localdate() + timedelta(days=1),
        preferred_period=TrialClassRequest.PERIOD_EVENING,
        status=TrialClassRequest.STATUS_REQUESTED,
    )
    client.force_login(admin_user)

    response = client.get(reverse("system:admin-dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Dashboard administrativo" in content
    assert "KPIs principais" in content
    assert overdue_invoice.subscription.responsible_user.full_name in content
    assert "Lead Dashboard" in content


@pytest.mark.django_db
def test_admin_dashboard_filters_kpis_by_selected_month(client):
    admin_user = AdminUserFactory(password="StrongPassword123")
    today = timezone.localdate()
    previous_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    current_invoice = MonthlyInvoiceFactory(status=MonthlyInvoice.STATUS_PAID, amount_net=Decimal("180.00"))
    previous_invoice = MonthlyInvoiceFactory(status=MonthlyInvoice.STATUS_PAID, amount_net=Decimal("320.00"))
    current_invoice.paid_at = _midday(today)
    previous_invoice.paid_at = _midday(previous_month + timedelta(days=2))
    current_invoice.save(update_fields=["paid_at", "updated_at"])
    previous_invoice.save(update_fields=["paid_at", "updated_at"])
    client.force_login(admin_user)

    response = client.get(reverse("system:admin-dashboard"), {"month": previous_month.strftime("%Y-%m")})
    snapshot = response.context["snapshot"]

    assert response.status_code == 200
    assert response.context["selected_month"] == previous_month.strftime("%Y-%m")
    assert snapshot.snapshot_date == previous_month
    assert snapshot.paid_revenue_total == previous_invoice.amount_net
