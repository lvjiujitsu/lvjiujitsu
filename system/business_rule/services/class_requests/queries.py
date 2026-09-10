from django.db.models import Q
from system.business_rule.models import ClassCatalogRequest, ClassCatalogRequestStatus


def get_class_catalog_requests_for_person(person, limit=5):
    if person is None:
        return []
    return list(
        ClassCatalogRequest.objects.filter(
            requester_person=person,
        )
        .select_related("target_class_group", "created_class_group")
        .order_by("-created_at")[:limit]
    )


def get_class_catalog_requests_history_for_person(person, limit=20):
    if person is None:
        return []
    return list(
        ClassCatalogRequest.objects.filter(
            Q(requester_person=person) | Q(teacher_person=person) | Q(created_teacher=person)
        )
        .select_related("target_class_group", "created_class_group")
        .order_by("-created_at")
        .distinct()[:limit]
    )


def get_pending_class_catalog_request_count():
    return ClassCatalogRequest.objects.filter(
        status=ClassCatalogRequestStatus.PENDING,
    ).count()
