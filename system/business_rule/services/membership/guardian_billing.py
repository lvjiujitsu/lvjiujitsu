from system.business_rule.models.membership import MembershipInvoice
from system.business_rule.models.person import PersonRelationship, PersonRelationshipKind
from system.business_rule.services.membership.queries import get_active_membership, get_active_memberships_for_people, get_latest_open_order, get_membership_owner


def get_guardian_billing_tabs(guardian_person):
    dependents_qs = (
        PersonRelationship.objects.filter(
            source_person=guardian_person,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        .select_related("target_person")
        .order_by("target_person__full_name")
    )
    dependents = [rel.target_person for rel in dependents_qs]
    memberships_by_person = get_active_memberships_for_people([guardian_person, *dependents])
    tabs = [
        _build_billing_tab(
            guardian_person,
            is_active=True,
            memberships_by_person=memberships_by_person,
        )
    ]
    for dependent in dependents:
        tabs.append(
            _build_billing_tab(
                dependent,
                is_active=False,
                memberships_by_person=memberships_by_person,
            )
        )
    return tabs


def build_guardian_billing_tabs_cached(guardian, dependent_people, memberships_by_person):
    tabs = [
        _build_billing_tab(
            guardian,
            is_active=True,
            memberships_by_person=memberships_by_person,
        )
    ]
    for dependent in dependent_people:
        tabs.append(
            _build_billing_tab(
                dependent,
                is_active=False,
                memberships_by_person=memberships_by_person,
            )
        )
    return tabs


def _build_billing_tab(person, *, is_active=False, memberships_by_person=None):
    billing_owner = get_membership_owner(person)
    active_membership = get_active_membership(
        person,
        billing_owner=billing_owner,
        memberships_by_person=memberships_by_person,
    )
    pending_order = get_latest_open_order(person)
    recent_invoices = []
    if active_membership is not None:
        recent_invoices = list(
            MembershipInvoice.objects.filter(membership=active_membership)
            .order_by("-paid_at", "-created_at")[:5]
        )
    return {
        "person": person,
        "active_membership": active_membership,
        "pending_order": pending_order,
        "recent_invoices": recent_invoices,
        "is_active_tab": is_active,
        "billing_owner": billing_owner,
    }
