import secrets

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from system.models import DocumentRecord, LgpdRequest, LocalSubscription, PaymentProof, StudentProfile, SystemUser


@transaction.atomic
def confirm_lgpd_request(*, lgpd_request, actor_user):
    _validate_request_owner(lgpd_request, actor_user)
    if lgpd_request.confirmed_at:
        return lgpd_request
    lgpd_request.confirmed_at = timezone.now()
    lgpd_request.save(update_fields=["confirmed_at", "updated_at"])
    return lgpd_request


@transaction.atomic
def process_lgpd_request(*, lgpd_request, actor_user, approve, processing_notes=""):
    _validate_processable_request(lgpd_request)
    if not approve:
        return _reject_request(lgpd_request, actor_user, processing_notes)
    summary = _build_processing_summary(lgpd_request, actor_user)
    lgpd_request.status = LgpdRequest.STATUS_COMPLETED
    lgpd_request.processed_by = actor_user
    lgpd_request.processing_notes = processing_notes
    lgpd_request.result_summary = summary
    lgpd_request.resolved_at = timezone.now()
    lgpd_request.save(
        update_fields=[
            "status",
            "processed_by",
            "processing_notes",
            "result_summary",
            "resolved_at",
            "updated_at",
        ]
    )
    return lgpd_request


def _validate_request_owner(lgpd_request, actor_user):
    if lgpd_request.user_id != actor_user.id:
        raise ValidationError("Somente o titular da solicitacao pode confirma-la.")


def _validate_processable_request(lgpd_request):
    if lgpd_request.status not in {LgpdRequest.STATUS_OPEN, LgpdRequest.STATUS_IN_PROGRESS}:
        raise ValidationError("A solicitacao ja foi encerrada.")
    if lgpd_request.requires_confirmation and not lgpd_request.is_confirmed:
        raise ValidationError("A solicitacao precisa de confirmacao explicita do titular.")


def _reject_request(lgpd_request, actor_user, processing_notes):
    lgpd_request.status = LgpdRequest.STATUS_REJECTED
    lgpd_request.processed_by = actor_user
    lgpd_request.processing_notes = processing_notes
    lgpd_request.resolved_at = timezone.now()
    lgpd_request.save(
        update_fields=["status", "processed_by", "processing_notes", "resolved_at", "updated_at"]
    )
    return lgpd_request


def _build_processing_summary(lgpd_request, actor_user):
    if lgpd_request.request_type in {LgpdRequest.TYPE_ACCESS, LgpdRequest.TYPE_CORRECTION}:
        return _build_non_destructive_summary(actor_user)
    return anonymize_user_data(user=lgpd_request.user, actor_user=actor_user)


def _build_non_destructive_summary(actor_user):
    return {
        "processed_by": actor_user.cpf,
        "processed_at": timezone.now().isoformat(),
        "mode": "non_destructive",
    }


@transaction.atomic
def anonymize_user_data(*, user, actor_user):
    _validate_anonymization_preconditions(user)
    summary = {
        "processed_by": actor_user.cpf,
        "processed_at": timezone.now().isoformat(),
        "document_files_removed": _clear_document_files(user),
        "payment_proof_files_removed": _clear_payment_proof_files(user),
        "student_profiles_anonymized": _anonymize_student_profiles(user),
    }
    _anonymize_guardian_links(user)
    _anonymize_identity(user)
    return summary


def _validate_anonymization_preconditions(user):
    active_statuses = (
        LocalSubscription.STATUS_DRAFT,
        LocalSubscription.STATUS_ACTIVE,
        LocalSubscription.STATUS_PENDING_FINANCIAL,
        LocalSubscription.STATUS_PAUSED,
        LocalSubscription.STATUS_BLOCKED,
    )
    if user.financial_subscriptions.filter(status__in=active_statuses).exists():
        raise ValidationError("Finalize os contratos financeiros antes de anonimizar este cadastro.")


def _clear_document_files(user):
    documents = DocumentRecord.objects.filter(owner_user=user)
    return _clear_file_records(documents, original_filename="[anonimizado]")


def _clear_payment_proof_files(user):
    proofs = PaymentProof.objects.filter(uploaded_by=user)
    count = 0
    for proof in proofs:
        _delete_file(proof.file)
        proof.file.name = ""
        proof.original_filename = "[anonimizado]"
        proof.save(update_fields=["file", "original_filename", "updated_at"])
        count += 1
    return count


def _anonymize_student_profiles(user):
    count = 0
    for student in StudentProfile.objects.filter(user=user).select_related("emergency_record"):
        _clear_emergency_record(student)
        student.contact_phone = ""
        student.self_service_access = False
        student.is_active = False
        student.operational_status = StudentProfile.STATUS_INACTIVE
        student.notes = _append_anonymization_note(student.notes)
        student.save(
            update_fields=[
                "contact_phone",
                "self_service_access",
                "is_active",
                "operational_status",
                "notes",
                "updated_at",
            ]
        )
        count += 1
    return count


def _anonymize_guardian_links(user):
    links = user.dependent_links_as_responsible.filter(end_date__isnull=True)
    for link in links:
        link.end_date = timezone.localdate()
        link.notes = _append_anonymization_note(link.notes)
        link.save(update_fields=["end_date", "notes", "updated_at"])


def _anonymize_identity(user):
    user.full_name = _build_anonymized_name(user)
    user.email = None
    user.cpf = _generate_unique_anonymized_cpf()
    user.timezone = "America/Sao_Paulo"
    user.is_active = False
    user.must_change_password = False
    user.set_unusable_password()
    user.save(
        update_fields=[
            "full_name",
            "email",
            "cpf",
            "timezone",
            "is_active",
            "must_change_password",
            "password",
            "updated_at",
        ]
    )


def _clear_emergency_record(student):
    record = getattr(student, "emergency_record", None)
    if record is None:
        return
    record.emergency_contact_name = "[anonimizado]"
    record.emergency_contact_phone = "00000000000"
    record.emergency_contact_relationship = "[anonimizado]"
    record.blood_type = ""
    record.allergies = ""
    record.medications = ""
    record.medical_notes = ""
    record.save(
        update_fields=[
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "blood_type",
            "allergies",
            "medications",
            "medical_notes",
            "updated_at",
        ]
    )


def _clear_file_records(records, *, original_filename):
    count = 0
    for record in records:
        _delete_file(record.file)
        record.file.name = ""
        record.original_filename = original_filename
        record.save(update_fields=["file", "original_filename", "updated_at"])
        count += 1
    return count


def _delete_file(file_field):
    if not file_field:
        return
    try:
        file_field.delete(save=False)
    except FileNotFoundError:
        return


def _append_anonymization_note(current_notes):
    prefix = "Cadastro anonimizado por solicitacao LGPD."
    return prefix if not current_notes else f"{current_notes}\n{prefix}"


def _build_anonymized_name(user):
    return f"Anonimizado {user.uuid.hex[:8].upper()}"


def _generate_unique_anonymized_cpf():
    while True:
        generated = f"{secrets.randbelow(10**11):011d}"
        if not SystemUser.objects.filter(cpf=generated).exists():
            return generated
