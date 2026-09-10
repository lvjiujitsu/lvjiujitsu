from datetime import timedelta
from decimal import Decimal
from system.business_rule.models.calendar import (
    CheckinStatus,
    ClassCheckin,
    SessionStatus,
    SpecialClassCheckin,
)
from system.business_rule.models.class_membership import ClassEnrollment, EnrollmentStatus
from system.business_rule.models.registration_order import PaymentStatus, RegistrationOrder
from system.business_rule.models import PersonRelationship
from system.business_rule.services.payroll_rules.constants import PAYROLL_SCOPE_ALL
from system.business_rule.services.payroll_rules.helpers import eligible_paid_cutoff, money, month_bounds, payout_available_on


def get_staff_class_group_ids(person):
    primary_ids = set(
        person.primary_class_groups.filter(is_active=True).values_list("pk", flat=True)
    )
    assignment_ids = set(
        person.class_instructor_assignments
        .filter(class_group__is_active=True)
        .values_list("class_group_id", flat=True)
    )
    return primary_ids | assignment_ids


def matching_group_ids(rule, person_group_ids):
    if rule["scope"] == PAYROLL_SCOPE_ALL:
        return person_group_ids
    group_id = rule.get("class_group_id")
    if group_id and int(group_id) in person_group_ids:
        return {int(group_id)}
    return set()


def rule_applies_to_person(rule, group_ids):
    return rule["scope"] == PAYROLL_SCOPE_ALL or bool(group_ids)


def _count_active_students(group_ids, reference_month):
    return len(_active_student_ids(group_ids, reference_month))


def _active_student_ids(group_ids, reference_month):
    if not group_ids:
        return set()
    _, period_end = month_bounds(reference_month)
    return set(
        ClassEnrollment.objects.filter(
            class_group_id__in=group_ids,
            status=EnrollmentStatus.ACTIVE,
            created_at__date__lte=period_end,
        ).values_list("person_id", flat=True)
    )


def get_paid_student_entries(group_ids, reference_month, *, as_of_date):
    cutoff = eligible_paid_cutoff(reference_month, as_of_date)
    period_start, _ = month_bounds(reference_month)
    if not group_ids or cutoff < period_start:
        return []
    orders = _get_student_entry_orders(
        period_start=period_start,
        period_end=cutoff,
    )
    return _build_student_entries_from_orders(orders, group_ids, active_only=True)


def get_held_student_entries(group_ids, reference_month, *, as_of_date):
    if not group_ids:
        return []
    period_start, period_end = month_bounds(reference_month)
    cutoff = eligible_paid_cutoff(reference_month, as_of_date)
    start = period_start
    if cutoff >= period_start:
        start = cutoff + timedelta(days=1)
    end = min(period_end, as_of_date)
    if end < start:
        return []
    orders = _get_student_entry_orders(period_start=start, period_end=end)
    return _build_student_entries_from_orders(orders, group_ids, active_only=True)


def _get_student_entry_orders(*, period_start, period_end):
    return (
        RegistrationOrder.objects.filter(
            payment_status=PaymentStatus.PAID,
            paid_at__date__gte=period_start,
            paid_at__date__lte=period_end,
            total__gt=0,
        )
        .select_related("person", "plan")
        .order_by("paid_at", "pk")
    )


def _build_student_entries_from_orders(orders, group_ids, *, active_only):
    if not orders:
        return []
    students_by_billing_person = _preload_students_for_orders(
        orders,
        group_ids,
        active_only=active_only,
    )
    entries = []
    for order in orders:
        linked_students = students_by_billing_person.get(order.person_id, [])
        if not linked_students:
            continue
        order_amount = money(order.net_amount if order.net_amount else order.total)
        allocated = money(order_amount / Decimal(len(linked_students)))
        for student in linked_students:
            entries.append(
                {
                    "person": student,
                    "order": order,
                    "amount": allocated,
                    "expected_deposit_date": order.expected_deposit_date,
                    "paid_at": order.paid_at,
                    "payout_available_on": payout_available_on(order),
                }
            )
    return entries


def _preload_students_for_orders(orders, group_ids, *, active_only):

    billing_person_ids = {order.person_id for order in orders}
    dependent_map = {}
    if billing_person_ids:
        for source_id, target_id in PersonRelationship.objects.filter(
            source_person_id__in=billing_person_ids,
        ).values_list("source_person_id", "target_person_id"):
            dependent_map.setdefault(source_id, set()).add(target_id)

    candidate_ids = set(billing_person_ids)
    for dependent_ids in dependent_map.values():
        candidate_ids.update(dependent_ids)

    enrollments = ClassEnrollment.objects.filter(
        person_id__in=candidate_ids,
        class_group_id__in=group_ids,
    )
    if active_only:
        enrollments = enrollments.filter(status=EnrollmentStatus.ACTIVE)
    enrollments = enrollments.select_related("person").order_by(
        "person__full_name",
        "person_id",
    )

    students_by_person = {}
    for enrollment in enrollments:
        bucket = students_by_person.setdefault(enrollment.person_id, [])
        if enrollment.person_id not in {student.pk for student in bucket}:
            bucket.append(enrollment.person)

    students_by_billing_person = {}
    for order in orders:
        candidate_person_ids = {order.person_id}
        candidate_person_ids.update(dependent_map.get(order.person_id, set()))
        linked_students = []
        seen = set()
        for person_id in candidate_person_ids:
            for student in students_by_person.get(person_id, []):
                if student.pk in seen:
                    continue
                linked_students.append(student)
                seen.add(student.pk)
        students_by_billing_person[order.person_id] = linked_students
    return students_by_billing_person


def get_order_students_for_groups(billing_person, group_ids, *, active_only=True):
    candidate_ids = {billing_person.pk}
    candidate_ids.update(
        billing_person.outgoing_relationships.values_list("target_person_id", flat=True)
    )
    enrollments = ClassEnrollment.objects.filter(
        person_id__in=candidate_ids,
        class_group_id__in=group_ids,
    )
    if active_only:
        enrollments = enrollments.filter(status=EnrollmentStatus.ACTIVE)
    enrollments = enrollments.select_related("person").order_by(
        "person__full_name",
        "person_id",
    )
    students = []
    seen = set()
    for enrollment in enrollments:
        if enrollment.person_id in seen:
            continue
        students.append(enrollment.person)
        seen.add(enrollment.person_id)
    return students


def count_class_attendances(person, group_ids, reference_month, *, include_special):
    period_start, period_end = month_bounds(reference_month)
    total = 0
    if group_ids:
        total += (
            ClassCheckin.objects.filter(
                session__schedule__class_group_id__in=group_ids,
                session__date__gte=period_start,
                session__date__lte=period_end,
                status=CheckinStatus.APPROVED,
            )
            .exclude(session__status=SessionStatus.CANCELLED)
            .count()
        )
    if include_special:
        total += (
            SpecialClassCheckin.objects.filter(
                special_class__teacher=person,
                special_class__date__gte=period_start,
                special_class__date__lte=period_end,
                status=CheckinStatus.APPROVED,
            )
            .exclude(special_class__status=SessionStatus.CANCELLED)
            .count()
        )
    return total
