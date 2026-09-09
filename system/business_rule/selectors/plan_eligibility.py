from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from system.business_rule.models.category import CategoryAudience
from system.business_rule.models.class_group import ClassGroup
from system.business_rule.models.class_membership import ClassEnrollment, EnrollmentStatus
from system.business_rule.models.person import Person, PersonRelationship, PersonRelationshipKind
from system.business_rule.models.plan import PlanAudience, SubscriptionPlan
from system.business_rule.models.plan import PlanPrice
from system.business_rule.models.membership import Membership


KIDS_JUVENILE_CATEGORY_AUDIENCES = {CategoryAudience.KIDS, CategoryAudience.JUVENILE}
ADULT_CATEGORY_AUDIENCES = {CategoryAudience.ADULT, CategoryAudience.WOMEN}
ADULT_AGE_THRESHOLD = 18


@dataclass(frozen=True)
class PlanEligibilityContext:
    adult_active: bool
    kids_juvenile_active_count: int
    allow_special_authorization: bool = False
    veteran_eligible: bool = False
    adult_active_count: int = 0

    @property
    def total_active_count(self) -> int:
        return self.resolved_adult_active_count + self.kids_juvenile_active_count

    @property
    def resolved_adult_active_count(self) -> int:
        if self.adult_active_count > 0:
            return self.adult_active_count
        return 1 if self.adult_active else 0

    @property
    def adult_family_group_eligible(self) -> bool:
        return self.resolved_adult_active_count > 0 and self.total_active_count >= 2

    @property
    def kids_family_group_eligible(self) -> bool:
        return self.kids_juvenile_active_count >= 2


def compute_veteran_member_since(person, *, reference_date=None):
    if person is None:
        return None


    reference = reference_date or timezone.now()
    grace = timedelta(days=settings.VETERAN_PLAN_GAP_GRACE_DAYS)

    stints = []
    memberships = Membership.objects.filter(
        person=person,
        activated_at__isnull=False,
    ).order_by("activated_at")
    for membership in memberships:
        start = membership.activated_at
        end = membership.canceled_at or membership.current_period_end
        if end is not None and end < start:
            end = start
        stints.append((start, end))

    if not stints:
        return None

    current_start = stints[0][0]
    previous_end = stints[0][1] or reference
    for start, end in stints[1:]:
        if start - previous_end > grace:
            current_start = start
        previous_end = max(previous_end, end or reference)
    return current_start


def is_veteran_plan_eligible(person, *, reference_date=None) -> bool:
    if person is None:
        return False
    if getattr(person, "veteran_plan_approved", False):
        return True
    member_since = compute_veteran_member_since(person, reference_date=reference_date)
    if member_since is None:
        return False
    reference = reference_date or timezone.now()
    tenure_threshold = timedelta(days=365 * settings.VETERAN_PLAN_TENURE_YEARS)
    return (reference - member_since) >= tenure_threshold


def get_eligible_plans(context: PlanEligibilityContext, *, base_queryset=None):
    queryset = base_queryset if base_queryset is not None else SubscriptionPlan.objects.filter(
        is_active=True
    )

    if not context.allow_special_authorization:
        queryset = queryset.exclude(requires_special_authorization=True)

    if not context.veteran_eligible:
        queryset = queryset.exclude(is_loyalty_plan=True)

    audience_filter = _build_audience_filter(context)
    if audience_filter is None:
        return queryset.none()

    return queryset.filter(audience_filter).order_by("display_order", "price")


def get_eligible_plan_prices(context: PlanEligibilityContext):

    audiences = []
    if context.adult_active:
        audiences.append(PlanAudience.ADULT)
    if context.kids_juvenile_active_count >= 1:
        audiences.append(PlanAudience.KIDS_JUVENILE)
    if not audiences:
        return PlanPrice.objects.none()

    return (
        PlanPrice.objects.filter(
            is_active=True, tier__is_active=True, tier__audience__in=audiences
        )
        .select_related("tier")
        .order_by("tier__display_order", "price")
    )


def is_plan_eligible(plan: SubscriptionPlan, context: PlanEligibilityContext) -> bool:
    if not context.allow_special_authorization and plan.requires_special_authorization:
        return False
    if plan.is_loyalty_plan and not context.veteran_eligible:
        return False
    if plan.audience == PlanAudience.ADULT:
        if not context.adult_active:
            return False
        return not plan.is_family_plan or context.adult_family_group_eligible
    if plan.audience == PlanAudience.KIDS_JUVENILE:
        if context.kids_juvenile_active_count < 1:
            return False
        return not plan.is_family_plan or context.kids_family_group_eligible
    return False


def classify_class_groups_audience(class_groups):
    adult_active = False
    kids_juvenile_count = 0
    for class_group in class_groups:
        if class_group is None:
            continue
        audience = _get_audience_from_class_group(class_group)
        if audience in ADULT_CATEGORY_AUDIENCES:
            adult_active = True
        elif audience in KIDS_JUVENILE_CATEGORY_AUDIENCES:
            kids_juvenile_count += 1
    return adult_active, kids_juvenile_count


def classify_audience_from_age(birth_date, *, reference_date=None) -> str:
    if birth_date is None:
        return ""
    person = Person(birth_date=birth_date)
    age = person.get_age(reference_date=reference_date)
    if age is None:
        return ""
    if age < ADULT_AGE_THRESHOLD:
        return PlanAudience.KIDS_JUVENILE
    return PlanAudience.ADULT


def build_eligibility_context_for_registration(cleaned_data, *, allow_special_authorization=False):
    profile = cleaned_data.get("registration_profile") or ""
    holder_groups = list(cleaned_data.get("holder_class_groups") or [])
    dependent_groups = list(cleaned_data.get("dependent_class_groups") or [])
    student_groups = list(cleaned_data.get("student_class_groups") or [])
    extra_dependents = cleaned_data.get("extra_dependents") or []
    include_dependent = bool(cleaned_data.get("include_dependent"))

    adult_active_count = 0
    kids_juvenile_count = 0

    if profile == "holder":
        holder_audience = _classify_groups_or_age(
            holder_groups,
            cleaned_data.get("holder_birthdate"),
        )
        if holder_audience == PlanAudience.ADULT:
            adult_active_count += 1
        elif holder_audience == PlanAudience.KIDS_JUVENILE:
            kids_juvenile_count += 1

        if include_dependent:
            dependent_audience = _classify_groups_or_age(
                dependent_groups,
                cleaned_data.get("dependent_birthdate"),
            )
            if dependent_audience == PlanAudience.ADULT:
                adult_active_count += 1
            elif dependent_audience == PlanAudience.KIDS_JUVENILE:
                kids_juvenile_count += 1

    elif profile == "guardian":
        student_audience = _classify_groups_or_age(
            student_groups,
            cleaned_data.get("student_birthdate"),
        )
        if student_audience == PlanAudience.ADULT:
            adult_active_count += 1
        elif student_audience == PlanAudience.KIDS_JUVENILE:
            kids_juvenile_count += 1

    for dependent in extra_dependents:
        dep_audience = _classify_groups_or_age(
            dependent.get("class_groups") or [],
            dependent.get("birth_date"),
        )
        if dep_audience == PlanAudience.ADULT:
            adult_active_count += 1
        elif dep_audience == PlanAudience.KIDS_JUVENILE:
            kids_juvenile_count += 1

    return PlanEligibilityContext(
        adult_active=adult_active_count > 0,
        adult_active_count=adult_active_count,
        kids_juvenile_active_count=kids_juvenile_count,
        allow_special_authorization=allow_special_authorization,
    )


def build_eligibility_context_for_person(person, *, allow_special_authorization=False):
    if person is None:
        return PlanEligibilityContext(
            adult_active=False,
            kids_juvenile_active_count=0,
            allow_special_authorization=allow_special_authorization,
        )

    family_people = _get_family_group_members(person)
    family_ids = [member.pk for member in family_people]
    hydrated_by_id = {
        p.pk: p
        for p in Person.objects.filter(pk__in=family_ids).select_related(
            "class_group__class_category", "class_category"
        )
    }
    enrollments_by_person_id = {}
    for enrollment in (
        ClassEnrollment.objects.filter(person_id__in=family_ids, status=EnrollmentStatus.ACTIVE)
        .select_related("class_group__class_category")
    ):
        enrollments_by_person_id.setdefault(enrollment.person_id, []).append(enrollment)

    adult_active_count = 0
    kids_juvenile_count = 0
    for member in family_people:
        member_audience = _classify_person_audience(
            hydrated_by_id.get(member.pk, member),
            active_enrollments=enrollments_by_person_id.get(member.pk, []),
        )
        if member_audience == PlanAudience.ADULT:
            adult_active_count += 1
        elif member_audience == PlanAudience.KIDS_JUVENILE:
            kids_juvenile_count += 1
    return PlanEligibilityContext(
        adult_active=adult_active_count > 0,
        adult_active_count=adult_active_count,
        kids_juvenile_active_count=kids_juvenile_count,
        allow_special_authorization=allow_special_authorization,
        veteran_eligible=is_veteran_plan_eligible(person),
    )


def _build_audience_filter(context: PlanEligibilityContext):
    audience_filter = None

    if context.adult_active:
        adult_filter = (
            Q(audience=PlanAudience.ADULT)
            if context.adult_family_group_eligible
            else Q(audience=PlanAudience.ADULT, is_family_plan=False)
        )
        audience_filter = adult_filter

    if context.kids_juvenile_active_count >= 1:
        kids_filter = (
            Q(audience=PlanAudience.KIDS_JUVENILE)
            if context.kids_family_group_eligible
            else Q(audience=PlanAudience.KIDS_JUVENILE, is_family_plan=False)
        )
        audience_filter = kids_filter if audience_filter is None else audience_filter | kids_filter

    return audience_filter


def _classify_groups_or_age(class_groups, birth_date):
    adult_active, kids_count = classify_class_groups_audience(class_groups)
    if adult_active:
        return PlanAudience.ADULT
    if kids_count > 0:
        return PlanAudience.KIDS_JUVENILE
    return classify_audience_from_age(birth_date)


def _classify_person_audience(person, *, active_enrollments=None):
    audiences = set()
    enrollments = (
        active_enrollments
        if active_enrollments is not None
        else person.class_enrollments.filter(
            status=EnrollmentStatus.ACTIVE,
        ).select_related("class_group__class_category")
    )
    for enrollment in enrollments:
        audience = _get_audience_from_class_group(enrollment.class_group)
        if audience:
            audiences.add(audience)
    if person.class_group_id:
        audience = _get_audience_from_class_group(person.class_group)
        if audience:
            audiences.add(audience)
    if person.class_category_id:
        audiences.add(person.class_category.audience)
    if audiences & ADULT_CATEGORY_AUDIENCES:
        return PlanAudience.ADULT
    if audiences & KIDS_JUVENILE_CATEGORY_AUDIENCES:
        return PlanAudience.KIDS_JUVENILE
    return classify_audience_from_age(person.birth_date)


def _get_audience_from_class_group(class_group):
    if isinstance(class_group, ClassGroup):
        if class_group.class_category_id is None:
            return ""
        return class_group.class_category.audience
    if isinstance(class_group, dict):
        category = class_group.get("class_category")
        return getattr(category, "audience", "")
    category = getattr(class_group, "class_category", None)
    return getattr(category, "audience", "")


def get_family_group_members(person):
    return _get_family_group_members(person)


def _get_family_group_members(person):
    members = {person.pk: person}
    related_qs = (
        PersonRelationship.objects.filter(
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        .filter(Q(source_person=person) | Q(target_person=person))
        .select_related("source_person", "target_person")
    )
    for relation in related_qs:
        for candidate in (relation.source_person, relation.target_person):
            if candidate.is_active and candidate.pk not in members:
                members[candidate.pk] = candidate
    return list(members.values())
