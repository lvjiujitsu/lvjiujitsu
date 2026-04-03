import pytest
from django.core.exceptions import ValidationError

from system.constants import ROLE_ALUNO_TITULAR, ROLE_PROFESSOR
from system.models import SystemRole
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.class_factories import ClassGroupFactory, InstructorProfileFactory
from system.tests.factories.student_factories import StudentProfileFactory


@pytest.mark.django_db
def test_instructor_profile_can_coexist_with_student_role():
    user = SystemUserFactory()
    student_role, _ = SystemRole.objects.get_or_create(code=ROLE_ALUNO_TITULAR, defaults={"name": "Titular"})
    professor_role, _ = SystemRole.objects.get_or_create(code=ROLE_PROFESSOR, defaults={"name": "Professor"})
    user.assign_role(student_role)
    user.assign_role(professor_role)
    StudentProfileFactory(user=user)

    instructor = InstructorProfileFactory(user=user)

    assert instructor.user == user
    assert user.has_any_role(ROLE_ALUNO_TITULAR, ROLE_PROFESSOR) is True


@pytest.mark.django_db
def test_class_group_validates_capacity_and_schedule():
    class_group = ClassGroupFactory.build(capacity=0, end_time="18:00")

    with pytest.raises(ValidationError):
        class_group.full_clean()
