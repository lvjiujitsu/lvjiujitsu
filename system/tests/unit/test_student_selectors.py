import pytest

from system.constants import ROLE_ALUNO_DEPENDENTE_COM_CREDENCIAL, ROLE_ALUNO_TITULAR, ROLE_RESPONSAVEL_FINANCEIRO
from system.models import SystemRole
from system.selectors.student_selectors import get_visible_students_for_user
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.finance_factories import LocalSubscriptionFactory, SubscriptionStudentFactory
from system.tests.factories.student_factories import GuardianRelationshipFactory, StudentProfileFactory


@pytest.mark.django_db
def test_holder_sees_own_profile_and_dependents():
    holder_user = SystemUserFactory()
    holder_role, _ = SystemRole.objects.get_or_create(code=ROLE_ALUNO_TITULAR, defaults={"name": "Titular"})
    holder_user.assign_role(holder_role)
    holder_profile = StudentProfileFactory(user=holder_user)
    dependent_profile = StudentProfileFactory(student_type="dependent")
    GuardianRelationshipFactory(student=dependent_profile, responsible_user=holder_user)

    visible_ids = list(get_visible_students_for_user(holder_user).values_list("id", flat=True))

    assert holder_profile.id in visible_ids
    assert dependent_profile.id in visible_ids


@pytest.mark.django_db
def test_dependent_with_credential_sees_only_self():
    dependent_user = SystemUserFactory()
    dependent_role, _ = SystemRole.objects.get_or_create(
        code=ROLE_ALUNO_DEPENDENTE_COM_CREDENCIAL,
        defaults={"name": "Dependente"},
    )
    dependent_user.assign_role(dependent_role)
    own_profile = StudentProfileFactory(user=dependent_user, student_type="dependent")
    other_profile = StudentProfileFactory()

    visible_ids = list(get_visible_students_for_user(dependent_user).values_list("id", flat=True))

    assert own_profile.id in visible_ids
    assert other_profile.id not in visible_ids


@pytest.mark.django_db
def test_financial_responsible_without_holder_role_sees_students_from_owned_contracts():
    responsible_user = SystemUserFactory()
    responsible_role, _ = SystemRole.objects.get_or_create(
        code=ROLE_RESPONSAVEL_FINANCEIRO,
        defaults={"name": "Responsavel financeiro"},
    )
    responsible_user.assign_role(responsible_role)
    subscription = LocalSubscriptionFactory(responsible_user=responsible_user)
    student_a = SubscriptionStudentFactory(subscription=subscription).student
    student_b = SubscriptionStudentFactory(subscription=subscription, is_primary_student=False).student

    visible_ids = list(get_visible_students_for_user(responsible_user).values_list("id", flat=True))

    assert student_a.id in visible_ids
    assert student_b.id in visible_ids
