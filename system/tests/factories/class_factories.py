import factory
from datetime import timedelta
from django.utils import timezone

from system.models import ClassDiscipline, ClassGroup, ClassSession, IbjjfBelt, InstructorProfile
from system.tests.factories.auth_factories import SystemUserFactory


class IbjjfBeltFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IbjjfBelt

    code = factory.Sequence(lambda index: f"belt_{index}")
    name = factory.Sequence(lambda index: f"Faixa {index}")
    display_order = factory.Sequence(lambda index: index + 10)
    is_active = True


class InstructorProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InstructorProfile

    user = factory.SubFactory(SystemUserFactory)
    belt_rank = factory.SubFactory(IbjjfBeltFactory)
    is_active = True


class ClassDisciplineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClassDiscipline

    name = factory.Sequence(lambda index: f"Modalidade {index}")
    slug = factory.Sequence(lambda index: f"modalidade-{index}")
    is_active = True


class ClassGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClassGroup

    name = factory.Sequence(lambda index: f"Turma {index}")
    modality = factory.SubFactory(ClassDisciplineFactory)
    instructor = factory.SubFactory(InstructorProfileFactory)
    reference_belt = factory.SubFactory(IbjjfBeltFactory)
    weekday = ClassGroup.WEEKDAY_MONDAY
    start_time = "19:00"
    end_time = "20:00"
    capacity = 20
    reservation_required = True
    minimum_age = 14
    is_active = True


class ClassSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClassSession

    class_group = factory.SubFactory(ClassGroupFactory)
    starts_at = factory.LazyFunction(timezone.now)
    ends_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    status = ClassSession.STATUS_SCHEDULED
