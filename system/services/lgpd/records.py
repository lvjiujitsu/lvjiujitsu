import secrets

from system.models import ConsentAcceptance, ConsentTerm, DocumentRecord, LgpdRequest, SensitiveAccessLog


def get_required_onboarding_terms():
    queryset = ConsentTerm.objects.filter(is_active=True, required_for_onboarding=True)
    queryset = queryset.order_by("code", "-version")
    latest_terms = {}
    for term in queryset:
        latest_terms.setdefault(term.code, term)
    return list(latest_terms.values())


def build_term_field_name(term):
    return f"term_{term.code}_{term.version}"


def record_term_acceptances(*, request, user, terms, context):
    payload = _extract_request_metadata(request)
    acceptances = []
    for term in terms:
        acceptance, _ = ConsentAcceptance.objects.get_or_create(
            user=user,
            term=term,
            defaults={
                "context": context,
                "ip_address": payload["ip_address"],
                "user_agent": payload["user_agent"],
            },
        )
        acceptances.append(acceptance)
    return acceptances


def create_lgpd_request(*, user, request_type, notes):
    request = LgpdRequest.objects.create(
        user=user,
        request_type=request_type,
        notes=notes,
        confirmation_code=_build_confirmation_code(),
    )
    return request


def register_document_record(
    *,
    owner_user,
    student,
    uploaded_by,
    uploaded_file,
    document_type,
    title,
    version_label="",
    subscription=None,
    is_visible_to_owner=True,
    notes="",
):
    document = DocumentRecord(
        owner_user=owner_user,
        student=student,
        uploaded_by=uploaded_by,
        file=uploaded_file,
        original_filename=uploaded_file.name,
        document_type=document_type,
        title=title,
        version_label=version_label,
        subscription=subscription,
        is_visible_to_owner=is_visible_to_owner,
        notes=notes,
    )
    document.full_clean()
    document.save()
    return document


def record_sensitive_access(*, actor_user, student, access_type, access_purpose, metadata=None):
    return SensitiveAccessLog.objects.create(
        actor_user=actor_user,
        student=student,
        access_type=access_type,
        access_purpose=access_purpose,
        metadata=metadata or {},
    )


def get_consent_history_for_user(user):
    queryset = user.consent_acceptances.select_related("term")
    return queryset.order_by("-accepted_at")


def _extract_request_metadata(request):
    return {
        "ip_address": _get_ip_address(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
    }


def _get_ip_address(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _build_confirmation_code():
    return secrets.token_hex(8).upper()
