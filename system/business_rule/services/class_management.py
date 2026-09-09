from django.db import transaction

from system.business_rule.models import ClassInstructorAssignment


@transaction.atomic
def save_class_group_catalog(*, form, schedule_formset):
    class_group = form.save(commit=False)
    class_group.save()
    sync_class_group_instructors(class_group, form.cleaned_data.get("assistant_staff"))

    schedule_formset.instance = class_group
    schedule_formset.save()
    return class_group


def sync_class_group_instructors(class_group, assistant_staff):
    selected_people = list(assistant_staff or [])
    selected_ids = {person.id for person in selected_people}

    ClassInstructorAssignment.objects.filter(class_group=class_group).exclude(
        person_id__in=selected_ids
    ).delete()

    for person in selected_people:
        ClassInstructorAssignment.objects.update_or_create(
            class_group=class_group,
            person=person,
            defaults={
                "is_primary": False,
                "notes": "Vínculo auxiliar configurado pelo cadastro de turma.",
            },
        )
