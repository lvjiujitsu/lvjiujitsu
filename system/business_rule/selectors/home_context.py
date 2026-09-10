from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from system.core.access import identity_of

from system.business_rule.access import TECHNICAL_ADMIN_KIND
from system.business_rule.constants import PersonTypeCode, Capability, STUDENT_PORTAL_PERSON_TYPE_CODES
from system.business_rule.forms import DependentProfileForm
from system.business_rule.models import Person
from system.business_rule.models.asaas import TeacherBankAccount, TeacherPayrollConfig, TeacherPayout
from system.business_rule.models.membership import MembershipInvoice
from system.business_rule.services.asaas_payroll import compute_available_balance
from system.business_rule.services.class_calendar import get_student_checkin_history, get_today_classes_for_person
from system.business_rule.services.graduation import compute_graduation_progress, get_graduation_history
from system.business_rule.services.membership import (
    get_active_membership,
    get_active_memberships_for_people,
    build_guardian_billing_tabs_cached,
    get_guardian_billing_tabs,
    get_latest_open_order,
    get_membership_owner,
    has_dependents,
)
from system.business_rule.services.payroll_rules import calculate_monthly_payroll
from system.business_rule.services.plan_change import (
    build_membership_summary,
    build_plan_catalog,
    build_plan_catalog_filters,
    get_plan_change_lock,
)
from system.business_rule.services.portal_capabilities import get_operational_role_labels
from system.business_rule.services.trial_access import get_active_trial_for_person
from system.business_rule.models.person import PersonRelationship, PersonRelationshipKind


def merge_class_entries(personal_entries, support_entries):
    seen_keys = set()
    merged = []
    for entry in list(personal_entries or []) + list(support_entries or []):
        key = (
            getattr(entry, "entry_role", None),
            getattr(entry, "schedule", None) and entry.schedule.pk,
            getattr(entry, "special_id", None),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(entry)
    merged.sort(key=lambda entry: entry.start_time or "")
    return merged


def client_profile_payload(person):
    address_parts = [
        person.address,
        person.address_number,
        person.address_complement,
        person.address_neighborhood,
        person.city,
    ]
    return {
        "full_name": person.full_name,
        "initial": (person.full_name[:1] or "").upper(),
        "cpf": person.cpf or "",
        "email": person.email or "",
        "phone": person.phone or "",
        "birth_date": date_format(person.birth_date, "SHORT_DATE_FORMAT") if person.birth_date else "",
        "address": ", ".join(part for part in address_parts if part),
    }


def build_belt_context(graduation_progress):
    if graduation_progress and graduation_progress.current_belt_rank:
        belt = graduation_progress.current_belt_rank
        grade = graduation_progress.current_grade_number or 0
        slots = belt.get_grade_slots(grade)
        slot_count = len(slots)
        tip_start, tip_width, stripe_w, stripe_gap = 232, 88, 12, 5
        if slot_count > 0:
            total_w = slot_count * stripe_w + (slot_count - 1) * stripe_gap
            sx = tip_start + (tip_width - total_w) // 2
            stripes = [
                {"filled": filled, "x": sx + index * (stripe_w + stripe_gap)}
                for index, filled in enumerate(slots)
            ]
        else:
            stripes = []
        return {
            "belt_rank": belt,
            "belt_grade_number": grade,
            "belt_stripes": stripes,
        }
    return {
        "belt_rank": None,
        "belt_grade_number": 0,
        "belt_stripes": [],
    }


def build_graduation_tabs(context):
    tabs = []
    if context.get("has_personal_area"):
        progress = context.get("graduation_progress")
        tab = {
            "person": context["client_person"],
            "graduation_progress": progress,
            "graduation_history": context.get("graduation_history") or [],
            "is_active_tab": True,
        }
        tab.update(build_belt_context(progress))
        tabs.append(tab)
    for dependent in context.get("dependents") or []:
        progress = dependent["graduation_progress"]
        tab = {
            "person": dependent["person"],
            "graduation_progress": progress,
            "graduation_history": dependent["graduation_history"],
            "is_active_tab": False,
        }
        tab.update(build_belt_context(progress))
        tabs.append(tab)
    return tabs


def build_today_classes_tabs(context):
    tabs = [{
        "person": context["client_person"],
        "class_items": context.get("my_classes") or [],
        "attendance_history": context.get("attendance_history") or [],
        "is_active_tab": True,
    }]
    for dependent in context.get("dependents") or []:
        tabs.append({
            "person": dependent["person"],
            "class_items": dependent["today_classes"],
            "attendance_history": get_student_checkin_history(dependent["person"]),
            "is_active_tab": False,
        })
    for index, tab in enumerate(tabs, start=1):
        tab["slug"] = f"turmas-{index}"
    return tabs


def build_attendance_history_items(context):
    tabs = context.get("today_classes_tabs") or []
    if len(tabs) > 1:
        items = []
        for tab in tabs:
            for entry in tab.get("attendance_history") or []:
                entry.person_id = tab["person"].pk
                items.append(entry)
        return items
    entries = context.get("attendance_history") or []
    for entry in entries:
        entry.person_id = None
    return entries


def build_profile_tabs(context):
    person = context.get("client_person")
    if person is None:
        return []
    billing_by_person_id = {
        tab["person"].pk: tab for tab in context.get("billing_tabs") or []
    }
    owner_billing = billing_by_person_id.get(person.pk, {})
    owner_form = context.get("client_profile_form")
    if owner_form is not None:
        owner_form.auto_id = "id_profile_1_%s"
    tabs = [{
        "person": person,
        "is_owner": True,
        "form": owner_form,
        "update_url": context.get("client_profile_update_url"),
        "active_membership": owner_billing.get("active_membership"),
        "pending_order": owner_billing.get("pending_order"),
        "billing_owner": None,
        "is_active_tab": True,
    }]
    for index, dependent in enumerate(context.get("dependents") or [], start=2):
        dep_person = dependent["person"]
        dep_billing = billing_by_person_id.get(dep_person.pk, {})
        tabs.append({
            "person": dep_person,
            "is_owner": False,
            "form": DependentProfileForm(instance=dep_person, auto_id=f"id_profile_{index}_%s"),
            "update_url": reverse("system:dependent-profile-update", args=[dep_person.pk]),
            "remove_url": dependent.get("remove_url"),
            "active_membership": dep_billing.get("active_membership", dependent.get("active_membership")),
            "pending_order": dep_billing.get("pending_order"),
            "billing_owner": dep_billing.get("billing_owner", dependent.get("billing_owner")),
            "is_active_tab": False,
        })
    return tabs


def build_billing_context(person, *, memberships_by_person=None, dependent_people=None):
    active_trial_access = get_active_trial_for_person(person)
    if dependent_people:
        billing_tabs = build_guardian_billing_tabs_cached(
            person,
            dependent_people,
            memberships_by_person or {},
        )
    elif has_dependents(person):
        billing_tabs = get_guardian_billing_tabs(person)
    else:
        if memberships_by_person is None:
            memberships_by_person = get_active_memberships_for_people([person])
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
        billing_tabs = [{
            "person": person,
            "active_membership": active_membership,
            "pending_order": pending_order,
            "recent_invoices": recent_invoices,
            "is_active_tab": True,
            "billing_owner": billing_owner,
        }]

    own_membership = None
    if memberships_by_person is not None:
        own_membership = memberships_by_person.get(person.pk)
    if own_membership is None:
        own_membership = get_active_membership(
            person,
            memberships_by_person=memberships_by_person,
        )
    plan_change_lock = get_plan_change_lock(own_membership)
    plan_change_locked = plan_change_lock["is_locked"]
    plan_change_catalog = (
        build_plan_catalog(person, own_membership)
        if own_membership and not plan_change_locked
        else []
    )
    plan_change_filters = build_plan_catalog_filters(plan_change_catalog)
    return {
        "active_trial_access": active_trial_access,
        "billing_tabs": billing_tabs,
        "client_billing_tab": billing_tabs[0] if billing_tabs else None,
        "plan_change_membership": own_membership,
        "plan_change_summary": build_membership_summary(own_membership),
        "plan_change_catalog": plan_change_catalog,
        "plan_change_filters": plan_change_filters,
        "plan_change_locked": plan_change_locked,
        "plan_change_available_on": plan_change_lock["available_on"],
        "plan_change_lock_message": plan_change_lock["message"],
    }


def build_payment_history_items(billing_tabs):
    items = []
    for tab in billing_tabs or []:
        membership = tab.get("active_membership")
        if membership is None:
            continue
        invoices = tab.get("recent_invoices")
        if invoices is None:
            invoices = (
                MembershipInvoice.objects.filter(membership=membership)
                .select_related("membership__plan", "membership__plan_price")
                .order_by("-paid_at", "-created_at")
            )
        for invoice in invoices:
            items.append({
                "person_id": tab["person"].pk,
                "person_name": tab["person"].full_name,
                "plan_name": membership.effective_display_name,
                "amount_paid": invoice.amount_paid,
                "amount_refunded": invoice.amount_refunded,
                "paid_at": invoice.paid_at,
                "status": invoice.status,
            })
    items.sort(key=lambda entry: entry["paid_at"] or timezone.now(), reverse=True)
    return items


def build_instructor_payroll_context(person):
    calculation = calculate_monthly_payroll(person)
    available, base, committed = compute_available_balance(person)
    recent_payouts = list(
        TeacherPayout.objects.filter(person=person)
        .order_by("-reference_month", "-created_at")[:10]
    )
    try:
        payroll_config = person.payroll_config
    except TeacherPayrollConfig.DoesNotExist:
        payroll_config = None
    try:
        payroll_bank = person.teacher_bank_account
    except TeacherBankAccount.DoesNotExist:
        payroll_bank = None
    return {
        "payroll_calculation": calculation,
        "payroll_available_balance": available,
        "payroll_base_salary": base,
        "payroll_committed_total": committed,
        "payroll_recent_payouts": recent_payouts,
        "payroll_config": payroll_config,
        "payroll_bank": payroll_bank,
    }


def build_dependents(guardian):

    dependents = []
    relationships = (
        PersonRelationship.objects.filter(
            source_person=guardian,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        .select_related("target_person", "target_person__person_type")
        .order_by("target_person__full_name")
    )
    dependent_people = [relationship.target_person for relationship in relationships]
    memberships_by_person = get_active_memberships_for_people([guardian, *dependent_people])
    for relationship in relationships:
        dependent = relationship.target_person
        progress = compute_graduation_progress(dependent)
        billing_owner = get_membership_owner(dependent)
        dependents.append({
            "person": dependent,
            "graduation_progress": progress,
            "graduation_history": get_graduation_history(dependent),
            "today_classes": get_today_classes_for_person(dependent),
            "attendance_history": get_student_checkin_history(dependent, limit=5),
            "active_membership": get_active_membership(
                dependent,
                billing_owner=billing_owner,
                memberships_by_person=memberships_by_person,
            ),
            "billing_owner": billing_owner,
            "remove_url": reverse("system:dependent-remove", args=[dependent.pk]),
        })
    return dependents, dependent_people, memberships_by_person


def role_labels(person, is_instructor, is_administrative, can_support_classes):
    labels = []
    if is_administrative:
        labels.append("Administrativo")
    if is_instructor:
        labels.append("Professor")
    if can_support_classes and not is_instructor and not is_administrative:
        labels.extend(get_operational_role_labels(person))
    trains_as_student = False
    if person is not None:
        trains_as_student = bool(
            person.jiu_jitsu_belt
            or person.class_enrollments.filter(status="active").exists()
            or (
                person.person_type_id
                and person.person_type.code in STUDENT_PORTAL_PERSON_TYPE_CODES
            )
        )
    if trains_as_student and "Aluno" not in labels:
        labels.append("Aluno")
    if person is not None and person.person_type_id:
        code = person.person_type.code
        if code == "guardian" and "Responsável" not in labels:
            labels.append("Responsável")
    return labels


def empty_context():
    return {
        "has_personal_area": False,
        "needs_split": False,
        "my_classes": [],
        "personal_today_classes": [],
        "staff_today_classes": [],
        "staff_work_today_classes": [],
        "today_classes": [],
        "attendance_history": [],
        "graduation_progress": None,
        "graduation_history": [],
        "graduation_tabs": [],
        "today_classes_tabs": [],
        "attendance_history_items": [],
        "profile_tabs": [],
        "belt_rank": None,
        "belt_grade_number": 0,
        "belt_stripes": [],
        "active_trial_access": None,
        "billing_tabs": [],
        "payment_history_items": [],
        "client_billing_tab": None,
        "plan_change_membership": None,
        "plan_change_summary": None,
        "plan_change_catalog": [],
        "plan_change_filters": {"frequencies": [], "cycles": [], "methods": []},
        "plan_change_locked": False,
        "plan_change_available_on": None,
        "plan_change_lock_message": "",
        "dependents": [],
        "show_dependents_area": False,
        "show_billing_area": False,
        "dependent_add_url": "",
        "dependent_add_modal_url": "",
        "dependent_modal_open": False,
        "financial_dashboard": None,
        "pending_administrative_access_request_count": 0,
        "pending_class_catalog_request_count": 0,
        "administrative_access_requests": [],
        "class_catalog_requests": [],
        "payroll_calculation": None,
        "payroll_available_balance": None,
        "payroll_base_salary": None,
        "payroll_committed_total": None,
        "payroll_recent_payouts": [],
        "payroll_config": None,
        "payroll_bank": None,
        "instructor_attendance_count": 0,
        "instructor_choices": [],
        "today_classes_toolbar": "overview",
        "can_create_special_classes": False,
    }


def get_portal_display_name(request):
    actor = identity_of(request).actor
    person = actor.person if actor is not None else None
    if person is not None:
        first_name = person.full_name.split()[0] if person.full_name else person.full_name
        return first_name or person.full_name
    user = actor.technical_admin if actor is not None else None
    if user is not None:
        return user.get_short_name() or user.get_full_name() or user.get_username()
    return "LV"


def can_access_people(request):
    identity = identity_of(request)
    if identity.kind == TECHNICAL_ADMIN_KIND:
        return True
    return identity.has_any(Capability.SUPPORT_PEOPLE)


def can_manage_access_requests(request):
    identity = identity_of(request)
    if identity.kind == TECHNICAL_ADMIN_KIND:
        return True
    return identity.has_any(
        Capability.MANAGE_PEOPLE,
        Capability.MANAGE_ACADEMY,
    )


def can_manage_class_requests(request):
    identity = identity_of(request)
    if identity.kind == TECHNICAL_ADMIN_KIND:
        return True
    return identity.has_any(
        Capability.MANAGE_CLASSES,
        Capability.MANAGE_ACADEMY,
    )


def get_active_instructor_choices():
    return list(
        Person.objects.filter(
            person_type__code=PersonTypeCode.INSTRUCTOR,
            is_active=True,
        )
        .order_by("full_name")
        .values("pk", "full_name")
    )
