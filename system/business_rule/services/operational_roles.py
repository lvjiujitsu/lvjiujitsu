from django.db import transaction

from system.business_rule.constants import OperationalRoleCode
from system.business_rule.models import OperationalRole, PersonOperationalRole


@transaction.atomic
def sync_person_operational_roles(person, role_ids, class_assistant_group=None):
    selected_roles = list(
        OperationalRole.objects.filter(pk__in=role_ids, is_active=True)
    )
    desired_keys = set()
    for role in selected_roles:
        class_group = (
            class_assistant_group if role.code == OperationalRoleCode.CLASS_ASSISTANT else None
        )
        desired_keys.add((role.pk, class_group.pk if class_group else None))
        PersonOperationalRole.objects.update_or_create(
            person=person,
            role=role,
            class_group=class_group,
            defaults={"is_active": True},
        )
    for assignment in PersonOperationalRole.objects.filter(person=person):
        key = (assignment.role_id, assignment.class_group_id)
        if key not in desired_keys:
            assignment.delete()
