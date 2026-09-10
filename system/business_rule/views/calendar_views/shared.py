from system.business_rule.models.person import Person, PersonRelationship, PersonRelationshipKind


def resolve_checkin_actor(actor, body):
    person_id = body.get("person_id")
    if not person_id or int(person_id) == actor.pk:
        return actor
    is_dependent = PersonRelationship.objects.filter(
        source_person=actor,
        target_person_id=person_id,
        relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
    ).exists()
    if not is_dependent:
        raise ValueError("Pessoa inválida para este check-in.")
    return Person.objects.get(pk=person_id, is_active=True)
