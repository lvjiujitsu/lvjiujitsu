from django.db.models import Q
from django.utils import timezone

from system.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES
from system.models import Person
from system.services.graduation import compute_graduation_progress


def get_graduation_overview(reference_date=None, audience=None):
    reference_date = reference_date or timezone.localdate()
    queryset = Person.objects.filter(
        is_active=True,
        person_type__code__in=CLASS_ENROLLMENT_PERSON_TYPE_CODES,
    ).select_related("person_type")

    if audience:
        queryset = queryset.filter(
            Q(class_category__audience=audience)
            | Q(class_group__class_category__audience=audience)
        )

    rows = []
    for person in queryset.order_by("full_name"):
        progress = compute_graduation_progress(person, reference_date=reference_date)
        rows.append(progress)

    rows.sort(
        key=lambda r: (
            -1 if r.is_eligible else 0,
            -(r.progress_pct or 0),
            r.person.full_name,
        )
    )
    return rows
