import factory
from django.utils import timezone

from system.models import GraduationExam, GraduationExamParticipation, GraduationHistory, GraduationRule
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.class_factories import ClassDisciplineFactory, ClassGroupFactory, IbjjfBeltFactory
from system.tests.factories.student_factories import StudentProfileFactory


class GraduationRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GraduationRule

    scope = GraduationRule.SCOPE_INTERNAL
    discipline = factory.SubFactory(ClassDisciplineFactory)
    current_belt = factory.SubFactory(IbjjfBeltFactory)
    current_degree = 0
    target_belt = factory.SubFactory(IbjjfBeltFactory)
    target_degree = 0
    minimum_active_days = 30
    minimum_attendances = 8
    minimum_age = 0
    maximum_inactivity_days = 45
    requires_exam = True
    is_active = True


class GraduationHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GraduationHistory

    student = factory.SubFactory(StudentProfileFactory)
    belt_rank = factory.SubFactory(IbjjfBeltFactory)
    degree_level = 0
    started_on = factory.LazyFunction(timezone.localdate)
    ended_on = None
    is_current = True
    event_type = GraduationHistory.EVENT_INITIAL
    recorded_by = factory.SubFactory(SystemUserFactory)


class GraduationExamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GraduationExam

    title = factory.Sequence(lambda index: f"Exame de Graduacao {index}")
    scheduled_for = factory.LazyFunction(timezone.localdate)
    discipline = factory.SubFactory(ClassDisciplineFactory)
    class_group = factory.SubFactory(ClassGroupFactory)
    created_by = factory.SubFactory(SystemUserFactory)


class GraduationExamParticipationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GraduationExamParticipation

    exam = factory.SubFactory(GraduationExamFactory)
    student = factory.SubFactory(StudentProfileFactory)
    current_belt = factory.SubFactory(IbjjfBeltFactory)
    current_degree = 0
    suggested_belt = factory.SubFactory(IbjjfBeltFactory)
    suggested_degree = 0
    status = GraduationExamParticipation.STATUS_PENDING
