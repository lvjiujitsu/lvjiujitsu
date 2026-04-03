from django.db.models import Q

from system.models import ConsentAcceptance, DocumentRecord, GraduationExamParticipation, PaymentProof
from system.selectors.student_selectors import get_visible_students_for_user


def get_user_document_history(user):
    visible_students = list(get_visible_students_for_user(user))
    student_ids = [student.id for student in visible_students]
    return {
        "documents": _get_document_records_for_user(user, student_ids),
        "payment_proofs": _get_payment_proofs_for_students(student_ids),
        "certificates": _get_certificates_for_students(student_ids),
        "consent_history": _get_consent_history_for_user(user),
    }


def get_student_document_history(student):
    student_ids = [student.id]
    return {
        "documents": _get_document_records_for_student(student),
        "payment_proofs": _get_payment_proofs_for_students(student_ids),
        "certificates": _get_certificates_for_students(student_ids),
        "consent_history": _get_consent_history_for_user(student.user),
    }


def find_certificate_by_code(code):
    if not code:
        return None
    queryset = GraduationExamParticipation.objects.select_related(
        "exam",
        "student__user",
        "suggested_belt",
    )
    return queryset.filter(certificate_code=code.strip().upper()).first()


def _get_consent_history_for_user(user):
    queryset = ConsentAcceptance.objects.select_related("term")
    return queryset.filter(user=user).order_by("-accepted_at")


def _get_document_records_for_user(user, student_ids):
    queryset = DocumentRecord.objects.select_related("owner_user", "student__user", "subscription__plan")
    filters = Q(owner_user=user) | Q(student_id__in=student_ids)
    return queryset.filter(filters, is_visible_to_owner=True).distinct()


def _get_document_records_for_student(student):
    queryset = DocumentRecord.objects.select_related("owner_user", "student__user", "subscription__plan")
    filters = Q(student=student) | Q(owner_user=student.user)
    return queryset.filter(filters).distinct()


def _get_payment_proofs_for_students(student_ids):
    queryset = PaymentProof.objects.select_related(
        "invoice__subscription__plan",
        "uploaded_by",
        "reviewed_by",
    )
    queryset = queryset.filter(invoice__subscription__covered_students__student_id__in=student_ids)
    return queryset.distinct()


def _get_certificates_for_students(student_ids):
    queryset = GraduationExamParticipation.objects.select_related(
        "exam",
        "student__user",
        "suggested_belt",
    )
    queryset = queryset.filter(student_id__in=student_ids, certificate_code__isnull=False)
    return queryset.order_by("-certificate_issued_at", "-created_at")
