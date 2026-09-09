from django.db.models import Q
from django.utils import timezone

from system.business_rule.constants import CLASS_ENROLLMENT_PERSON_TYPE_CODES
from system.business_rule.models import Person
from system.business_rule.services.graduation import compute_graduation_progress_bulk


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

    persons = list(queryset.order_by("full_name"))
    progress_by_person_id = compute_graduation_progress_bulk(persons, reference_date=reference_date)
    rows = [progress_by_person_id[person.pk] for person in persons]

    rows.sort(
        key=lambda r: (
            -1 if r.is_eligible else 0,
            -(r.progress_pct or 0),
            r.person.full_name,
        )
    )
    return rows
