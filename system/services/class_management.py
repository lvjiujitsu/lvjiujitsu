from django.db import transaction


@transaction.atomic
def save_class_group_catalog(*, form, schedule_formset):
    class_group = form.save(commit=False)
    class_group.save()
    if hasattr(form, "save_related"):
        form.save_related(class_group)

    schedule_formset.instance = class_group
    schedule_formset.save()
    return class_group
