from django.db.models import Prefetch, Q

from system.models import GuardianRelationship, StudentProfile


def search_emergency_students(query):
    queryset = StudentProfile.objects.select_related("user", "emergency_record")
    queryset = queryset.prefetch_related(_guardian_prefetch())
    if not query:
        return queryset.none()
    filters = Q(user__full_name__icontains=query) | Q(user__cpf__icontains=query)
    return queryset.filter(filters, is_active=True).distinct()[:20]


def get_emergency_student(uuid):
    queryset = StudentProfile.objects.select_related("user", "emergency_record")
    queryset = queryset.prefetch_related(_guardian_prefetch())
    return queryset.filter(uuid=uuid, is_active=True).first()


def _guardian_prefetch():
    queryset = GuardianRelationship.objects.select_related("responsible_user")
    queryset = queryset.filter(end_date__isnull=True).order_by("-is_primary", "responsible_user__full_name")
    return Prefetch("guardian_links", queryset=queryset)
