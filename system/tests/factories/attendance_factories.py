import factory
from datetime import timedelta
from django.utils import timezone

from system.models import AttendanceQrToken, ClassReservation, PhysicalAttendance
from system.tests.factories.auth_factories import SystemUserFactory
from system.tests.factories.class_factories import ClassSessionFactory
from system.tests.factories.student_factories import StudentProfileFactory


class ClassReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClassReservation

    student = factory.SubFactory(StudentProfileFactory)
    session = factory.SubFactory(ClassSessionFactory)
    status = ClassReservation.STATUS_ACTIVE


class AttendanceQrTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttendanceQrToken

    session = factory.SubFactory(ClassSessionFactory)
    token = factory.Sequence(lambda index: f"token-{index}")
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=5))
    generated_by = factory.SubFactory(SystemUserFactory)


class PhysicalAttendanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PhysicalAttendance

    student = factory.SubFactory(StudentProfileFactory)
    session = factory.SubFactory(ClassSessionFactory)
    checkin_method = PhysicalAttendance.METHOD_QR
