from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.models import (
    ClassEnrollment,
    ClassGroup,
    ClassSchedule,
    IbjjfAgeCategory,
    Person,
    PersonType,
    PortalAccount,
    TrainingStyle,
    WeekdayCode,
)
from system.models.calendar import ClassCheckin, ClassSession, Holiday, SessionStatus
from system.models.category import CategoryAudience, ClassCategory
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY
from system.services.class_calendar import (
    get_calendar_month_data,
    get_today_classes_for_person,
    perform_checkin,
    toggle_session_cancel,
)

User = get_user_model()


class HolidayModelTestCase(TestCase):
    def test_create_holiday(self):
        h = Holiday.objects.create(date=date(2026, 1, 1), name="Ano Novo")
        self.assertEqual(str(h), "01/01/2026 — Ano Novo")
        self.assertTrue(h.is_active)

    def test_unique_date(self):
        Holiday.objects.create(date=date(2026, 12, 25), name="Natal")
        with self.assertRaises(Exception):
            Holiday.objects.create(date=date(2026, 12, 25), name="Duplicado")


class ClassSessionModelTestCase(TestCase):
    def setUp(self):
        self.category = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        self.group = ClassGroup.objects.create(
            code="test-group", display_name="Teste", class_category=self.category,
        )
        self.schedule = ClassSchedule.objects.create(
            class_group=self.group, weekday=WeekdayCode.MONDAY,
            start_time=time(19, 0), training_style=TrainingStyle.GI,
        )

    def test_create_session(self):
        session = ClassSession.objects.create(schedule=self.schedule, date=date(2026, 4, 13))
        self.assertFalse(session.is_cancelled)

    def test_cancel_session(self):
        session = ClassSession.objects.create(
            schedule=self.schedule, date=date(2026, 4, 13),
            status=SessionStatus.CANCELLED, cancellation_reason="Chuva",
        )
        self.assertTrue(session.is_cancelled)

    def test_unique_constraint(self):
        ClassSession.objects.create(schedule=self.schedule, date=date(2026, 4, 13))
        with self.assertRaises(Exception):
            ClassSession.objects.create(schedule=self.schedule, date=date(2026, 4, 13))


class CalendarServiceTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.category = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age", display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18, maximum_age=99,
        )
        self.group = ClassGroup.objects.create(
            code="adult-test", display_name="Turma Teste", class_category=self.category,
        )
        today = timezone.localdate()
        weekday_map = {
            0: WeekdayCode.MONDAY, 1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY, 3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY, 5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        self.schedule = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=weekday_map[today.weekday()],
            start_time=time(19, 0),
            training_style=TrainingStyle.GI,
        )
        self.person = Person.objects.create(
            full_name="Aluno Teste", cpf="111.111.111-11",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()
        ClassEnrollment.objects.create(
            class_group=self.group, person=self.person, status="active",
        )

    def test_get_today_classes(self):
        classes = get_today_classes_for_person(self.person)
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].group_name, "Turma Teste")
        self.assertFalse(classes[0].is_cancelled)
        self.assertFalse(classes[0].has_checked_in)

    def test_today_classes_cancelled_by_holiday(self):
        Holiday.objects.create(date=timezone.localdate(), name="Feriado Teste")
        classes = get_today_classes_for_person(self.person)
        self.assertEqual(len(classes), 1)
        self.assertTrue(classes[0].is_cancelled)
        self.assertEqual(classes[0].cancellation_reason, "Feriado Teste")

    def test_perform_checkin(self):
        checkin, created = perform_checkin(self.person, self.schedule.pk)
        self.assertTrue(created)
        self.assertEqual(checkin.person, self.person)

    def test_perform_checkin_idempotent(self):
        perform_checkin(self.person, self.schedule.pk)
        checkin, created = perform_checkin(self.person, self.schedule.pk)
        self.assertFalse(created)

    def test_checkin_blocked_on_holiday(self):
        Holiday.objects.create(date=timezone.localdate(), name="Feriado")
        with self.assertRaises(ValueError):
            perform_checkin(self.person, self.schedule.pk)

    def test_toggle_session_cancel(self):
        today = timezone.localdate()
        session = toggle_session_cancel(self.schedule.pk, today, "Motivo")
        self.assertTrue(session.is_cancelled)
        self.assertEqual(session.cancellation_reason, "Motivo")

        session = toggle_session_cancel(self.schedule.pk, today)
        self.assertFalse(session.is_cancelled)

    def test_calendar_month_data(self):
        today = timezone.localdate()
        data = get_calendar_month_data(today.year, today.month)
        self.assertEqual(data.year, today.year)
        self.assertEqual(data.month, today.month)
        self.assertTrue(len(data.days) >= 28)
        today_entry = [d for d in data.days if d.is_today]
        self.assertEqual(len(today_entry), 1)


class CalendarViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin",
        )
        self.admin_type = PersonType.objects.create(
            code="administrative-assistant", display_name="Administrativo",
        )
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.admin_person = Person.objects.create(
            full_name="Admin", cpf="111.111.111-11", person_type=self.admin_type,
        )
        self.admin_account = PortalAccount(person=self.admin_person)
        self.admin_account.set_password("123456")
        self.admin_account.save()
        self.student_person = Person.objects.create(
            full_name="Aluno", cpf="222.222.222-22", person_type=self.student_type,
            birth_date=date(2000, 1, 1),
        )
        self.student_account = PortalAccount(person=self.student_person)
        self.student_account.set_password("123456")
        self.student_account.save()

    def _login_as_admin(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.admin_account.pk
        session[TECHNICAL_ADMIN_SESSION_KEY] = True
        session.save()

    def _login_as_student(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.student_account.pk
        session.save()

    def test_admin_calendar_loads(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:admin-calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cronograma de Aulas")

    def test_admin_calendar_month_loads(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:admin-calendar-month", args=[2026, 4]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abril")

    def test_student_schedule_loads(self):
        self._login_as_student()
        response = self.client.get(reverse("system:student-schedule"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cronograma de Aulas")

    def test_student_dashboard_shows_today(self):
        self._login_as_student()
        response = self.client.get(reverse("system:student-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aulas do dia")

    def test_admin_dashboard_shows_cronograma(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:admin-home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cronograma")
