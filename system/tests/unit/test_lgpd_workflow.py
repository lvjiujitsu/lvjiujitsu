import pytest
from django.utils import timezone

from system.models import LgpdRequest, PaymentProof
from system.services.lgpd import confirm_lgpd_request, process_lgpd_request
from system.tests.factories import (
    AdminUserFactory,
    DocumentRecordFactory,
    EmergencyRecordFactory,
    LgpdRequestFactory,
    PaymentProofFactory,
    StudentProfileFactory,
    SystemUserFactory,
)


@pytest.mark.django_db
def test_confirm_lgpd_request_marks_confirmation_timestamp():
    user = SystemUserFactory()
    lgpd_request = LgpdRequestFactory(user=user, request_type=LgpdRequest.TYPE_DELETION, confirmed_at=None)

    confirm_lgpd_request(lgpd_request=lgpd_request, actor_user=user)
    lgpd_request.refresh_from_db()

    assert lgpd_request.confirmed_at is not None


@pytest.mark.django_db
def test_process_lgpd_request_anonymizes_user_and_clears_sensitive_files():
    admin = AdminUserFactory()
    user = SystemUserFactory(email="sensivel@example.com")
    student = StudentProfileFactory(user=user)
    EmergencyRecordFactory(student=student)
    document = DocumentRecordFactory(owner_user=user, student=student, uploaded_by=admin)
    proof = PaymentProofFactory(uploaded_by=user)
    lgpd_request = LgpdRequestFactory(
        user=user,
        request_type=LgpdRequest.TYPE_DELETION,
        confirmed_at=timezone.now(),
    )

    process_lgpd_request(
        lgpd_request=lgpd_request,
        actor_user=admin,
        approve=True,
        processing_notes="Direito confirmado.",
    )

    user.refresh_from_db()
    student.refresh_from_db()
    document.refresh_from_db()
    proof.refresh_from_db()
    lgpd_request.refresh_from_db()

    assert lgpd_request.status == LgpdRequest.STATUS_COMPLETED
    assert user.full_name.startswith("Anonimizado")
    assert user.email is None
    assert user.is_active is False
    assert student.operational_status == student.STATUS_INACTIVE
    assert student.emergency_record.allergies == ""
    assert document.file.name == ""
    assert proof.file.name == ""
    assert lgpd_request.result_summary["document_files_removed"] == 1
    assert lgpd_request.result_summary["payment_proof_files_removed"] == 1
