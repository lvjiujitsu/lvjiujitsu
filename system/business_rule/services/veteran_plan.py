from django.db import transaction
from django.utils import timezone


@transaction.atomic
def approve_veteran_plan(person, *, approved_by, notes=""):
    person.veteran_plan_approved = True
    person.veteran_plan_approved_by = approved_by
    person.veteran_plan_approved_at = timezone.now()
    person.veteran_plan_approved_notes = notes or ""
    person.save(
        update_fields=[
            "veteran_plan_approved",
            "veteran_plan_approved_by",
            "veteran_plan_approved_at",
            "veteran_plan_approved_notes",
            "updated_at",
        ]
    )
    return person


@transaction.atomic
def revoke_veteran_plan(person, *, revoked_by, notes=""):
    person.veteran_plan_approved = False
    person.veteran_plan_approved_by = revoked_by
    person.veteran_plan_approved_at = timezone.now()
    person.veteran_plan_approved_notes = notes or ""
    person.save(
        update_fields=[
            "veteran_plan_approved",
            "veteran_plan_approved_by",
            "veteran_plan_approved_at",
            "veteran_plan_approved_notes",
            "updated_at",
        ]
    )
    return person
