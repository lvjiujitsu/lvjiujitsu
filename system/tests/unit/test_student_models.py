import pytest
from django.core.exceptions import ValidationError

from system.constants import ROLE_PROFESSOR
from system.models import GuardianRelationship, StudentProfile, SystemRole
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_student_profile_coexists_with_other_roles():
    user = SystemUserFactory()
    role, _ = SystemRole.objects.get_or_create(code=ROLE_PROFESSOR, defaults={"name": "Professor"})
    user.assign_role(role)

    profile = StudentProfile.objects.create(
        user=user,
        student_type=StudentProfile.TYPE_HOLDER,
        operational_status=StudentProfile.STATUS_ACTIVE,
    )

    assert user.has_role(ROLE_PROFESSOR) is True
    assert profile.user == user


@pytest.mark.django_db
def test_only_one_active_primary_guardian_is_allowed():
    holder = StudentProfileFactory()
    first_guardian = SystemUserFactory()
    second_guardian = SystemUserFactory()
    GuardianRelationship.objects.create(
        responsible_user=first_guardian,
        student=holder,
        relationship_type=GuardianRelationship.RELATIONSHIP_GUARDIAN,
        is_primary=True,
    )

    link = GuardianRelationship(
        responsible_user=second_guardian,
        student=holder,
        relationship_type=GuardianRelationship.RELATIONSHIP_GUARDIAN,
        is_primary=True,
    )

    with pytest.raises(ValidationError):
        link.full_clean()
