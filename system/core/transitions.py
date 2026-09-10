PREVIOUS_ATTRIBUTE = "_previous_values"


def remember_previous(instance, *field_names):
    values = {}
    if instance.pk is not None:
        stored = (
            type(instance)
            .objects.filter(pk=instance.pk)
            .values(*field_names)
            .first()
        )
        if stored is not None:
            values = stored
    setattr(instance, PREVIOUS_ATTRIBUTE, values)
    return values


def previous_of(instance, field_name):
    return getattr(instance, PREVIOUS_ATTRIBUTE, {}).get(field_name)


def changed_to(instance, field_name, value):
    return (
        getattr(instance, field_name) == value
        and previous_of(instance, field_name) != value
    )


def changed_from(instance, field_name, value):
    return (
        previous_of(instance, field_name) == value
        and getattr(instance, field_name) != value
    )
