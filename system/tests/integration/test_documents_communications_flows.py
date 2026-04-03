import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from system.constants import ROLE_PROFESSOR
from system.models import CommunicationDelivery, ConsentAcceptance, DocumentRecord, LgpdRequest, NoticeBoardMessage, SensitiveAccessLog
from system.services.students.registry import ensure_role
from system.tests.factories import (
    AdminUserFactory,
    ConsentTermFactory,
    DocumentRecordFactory,
    EmergencyRecordFactory,
    GraduationExamParticipationFactory,
    LgpdRequestFactory,
    StudentProfileFactory,
    SystemUserFactory,
)


@pytest.mark.django_db
def test_profile_page_lists_document_history_and_confirms_lgpd_request(client):
    user = SystemUserFactory(password="StrongPassword123")
    student = StudentProfileFactory(user=user)
    term = ConsentTermFactory(title="Termo de uso")
    ConsentAcceptance.objects.create(user=user, term=term, context="profile")
    DocumentRecordFactory(owner_user=user, student=student, title="Contrato do aluno")
    lgpd_request = LgpdRequestFactory(user=user, request_type=LgpdRequest.TYPE_DELETION, confirmed_at=None)
    client.force_login(user)

    response = client.get(reverse("system:my-profile"))
    confirm_response = client.post(
        reverse("system:my-profile"),
        data={"action": "confirm_lgpd", "request_uuid": str(lgpd_request.uuid)},
    )
    lgpd_request.refresh_from_db()

    assert response.status_code == 200
    assert "Contrato do aluno" in response.content.decode()
    assert confirm_response.status_code == 302
    assert lgpd_request.confirmed_at is not None


@pytest.mark.django_db
def test_admin_can_upload_student_document_and_view_certificate_history(client):
    admin = AdminUserFactory()
    student = StudentProfileFactory()
    participation = GraduationExamParticipationFactory(
        student=student,
        status=GraduationExamParticipationFactory._meta.model.STATUS_APPROVED,
        certificate_code="CERT-LV-0001",
        certificate_issued_at=timezone.now(),
    )
    client.force_login(admin)

    upload_response = client.post(
        reverse("system:student-update", kwargs={"uuid": student.uuid}),
        data={
            "action": "document",
            "document-document_type": DocumentRecord.TYPE_CONTRACT,
            "document-title": "Contrato anual",
            "document-version_label": "2026.1",
            "document-file": SimpleUploadedFile("contract.pdf", b"contract", content_type="application/pdf"),
            "document-is_visible_to_owner": "on",
            "document-notes": "Assinado na recepcao",
        },
    )
    page_response = client.get(reverse("system:student-update", kwargs={"uuid": student.uuid}))

    assert upload_response.status_code == 302
    assert page_response.status_code == 200
    assert DocumentRecord.objects.filter(student=student, title="Contrato anual").exists()
    assert participation.certificate_code in page_response.content.decode()


@pytest.mark.django_db
def test_certificate_lookup_returns_matching_certificate(client):
    participation = GraduationExamParticipationFactory(
        status=GraduationExamParticipationFactory._meta.model.STATUS_APPROVED,
        certificate_code="GRAD-VALID-01",
        certificate_issued_at=timezone.now(),
    )

    response = client.post(
        reverse("system:certificate-lookup"),
        data={"certificate-certificate_code": participation.certificate_code},
    )

    assert response.status_code == 200
    assert participation.student.user.full_name in response.content.decode()
    assert participation.certificate_code in response.content.decode()


@pytest.mark.django_db
def test_admin_can_publish_notice_and_queue_bulk_communication(client, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    admin = AdminUserFactory()
    recipient = SystemUserFactory(password="StrongPassword123")
    StudentProfileFactory(user=recipient)
    starts_at = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
    client.force_login(admin)

    notice_response = client.post(
        reverse("system:communication-center"),
        data={
            "action": "notice",
            "notice-title": "Tatame fechado",
            "notice-body": "Hoje a limpeza sera iniciada mais cedo.",
            "notice-audience": "ALL_USERS",
            "notice-starts_at": starts_at,
            "notice-ends_at": "",
            "notice-is_active": "on",
        },
    )
    bulk_response = client.post(
        reverse("system:communication-center"),
        data={
            "action": "bulk",
            "bulk-title": "Lembrete de aula",
            "bulk-message": "Nao esquecer o kimono limpo.",
            "bulk-audience": "ALL_USERS",
            "bulk-channel": "PORTAL",
        },
    )

    assert notice_response.status_code == 200
    assert bulk_response.status_code == 200
    assert NoticeBoardMessage.objects.filter(title="Tatame fechado").exists()
    assert CommunicationDelivery.objects.filter(status=CommunicationDelivery.STATUS_SENT).exists()

    client.force_login(recipient)
    board_response = client.get(reverse("system:notice-board"))

    assert board_response.status_code == 200
    assert "Tatame fechado" in board_response.content.decode()


@pytest.mark.django_db
def test_admin_can_process_confirmed_lgpd_request(client):
    admin = AdminUserFactory()
    user = SystemUserFactory(password="StrongPassword123")
    lgpd_request = LgpdRequestFactory(
        user=user,
        request_type=LgpdRequest.TYPE_ACCESS,
        confirmed_at=timezone.now(),
    )
    client.force_login(admin)

    response = client.post(
        reverse("system:lgpd-request-process", kwargs={"uuid": lgpd_request.uuid}),
        data={
            "decision-decision": "approve",
            "decision-processing_notes": "Relatorio separado para atendimento.",
        },
    )
    lgpd_request.refresh_from_db()

    assert response.status_code == 302
    assert lgpd_request.status == LgpdRequest.STATUS_COMPLETED


@pytest.mark.django_db
def test_emergency_quick_access_requires_role_and_logs_access(client):
    student = StudentProfileFactory()
    EmergencyRecordFactory(student=student)
    regular_user = SystemUserFactory(password="StrongPassword123")
    professor_user = SystemUserFactory(password="StrongPassword123")
    ensure_role(professor_user, ROLE_PROFESSOR)

    client.force_login(regular_user)
    denied_response = client.get(reverse("system:emergency-quick-access"), data={"q": student.user.full_name})

    client.force_login(professor_user)
    allowed_response = client.get(
        reverse("system:emergency-quick-access"),
        data={"q": student.user.full_name, "student": student.uuid},
    )

    assert denied_response.status_code == 403
    assert allowed_response.status_code == 200
    assert SensitiveAccessLog.objects.filter(student=student, access_type=SensitiveAccessLog.ACCESS_EMERGENCY_VIEW).exists()
