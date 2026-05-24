import json
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
    WeekdayCode,
)
from system.models.category import CategoryAudience, ClassCategory
from system.models.calendar import CheckinStatus, ClassCheckin, ClassSession, SessionStatus
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY


class HomeDashboardTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.category = ClassCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            maximum_age=99,
        )
        self.group = ClassGroup.objects.create(
            display_name="Turma Teste",
            class_category=self.category,
        )
        self.schedule = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=self._today_weekday_code(),
            start_time=time(19, 0),
            training_style="gi",
        )
        self.student = Person.objects.create(
            full_name="Aluno Home",
            cpf="111.111.111-11",
            person_type=self.student_type,
            birth_date=date(2000, 1, 1),
            biological_sex="male",
        )
        self.account = PortalAccount.objects.create(person=self.student)
        self.account.set_password("123456")
        self.account.save()
        ClassEnrollment.objects.create(
            class_group=self.group,
            person=self.student,
            status="active",
        )

    def test_student_home_renders_checkin_notice_when_instructor_not_present(self):
        self._login_portal_account(self.account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("checkin-notice", content)
        self.assertNotIn('class="btn btn--secondary btn--sm js-checkin"', content)

    def test_student_home_renders_checkin_button_when_instructor_present(self):
        ClassSession.objects.create(
            schedule=self.schedule,
            date=timezone.localdate(),
            status=SessionStatus.SCHEDULED,
            instructor_present=True,
            instructor_checked_in_at=timezone.now(),
        )
        self._login_portal_account(self.account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn(reverse("system:student-checkin"), content)
        self.assertIn('class="btn btn--secondary btn--sm js-checkin"', content)
        self.assertIn(f'data-schedule-id="{self.schedule.pk}"', content)
        self.assertNotIn('href="#"', content)
        self.assertIn("system/js/dashboard.js", content)

    def test_student_home_renders_calendar_link(self):
        self._login_portal_account(self.account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn(f'href="{reverse("system:calendar")}"', content)
        self.assertIn(">Cronograma</a>", content)
        self.assertNotIn("Criar aulão", content)

    def test_attendance_history_modal_uses_structured_filters(self):
        teacher = Person.objects.create(
            full_name="Professor Home",
            cpf="222.222.222-22",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
            biological_sex="male",
        )
        self.group.main_teacher = teacher
        self.group.save(update_fields=["main_teacher"])
        session = ClassSession.objects.create(
            schedule=self.schedule,
            date=timezone.localdate(),
        )
        ClassCheckin.objects.create(
            session=session,
            person=self.student,
            status=CheckinStatus.APPROVED,
            approved_at=timezone.now(),
        )
        self._login_portal_account(self.account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('class="attendance-history-filters"', content)
        self.assertIn('class="modal__select js-attendance-history-class"', content)
        self.assertIn('class="modal__select js-attendance-history-teacher"', content)
        self.assertIn('class="modal__select js-attendance-history-month"', content)
        self.assertIn('class="modal__select js-attendance-history-year"', content)
        self.assertIn('data-class-filter="Turma Teste · Adulto"', content)
        self.assertIn('data-teacher-filter="Professor Home"', content)
        self.assertIn(f'data-year-filter="{timezone.localdate().year}"', content)
        self.assertNotIn('type="search"', content)

    def test_student_checkin_endpoint_creates_pending_checkin(self):
        self._login_portal_account(self.account)

        response = self.client.post(
            reverse("system:student-checkin"),
            data=json.dumps({"schedule_id": self.schedule.pk}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ClassCheckin.objects.filter(
                person=self.student,
                session__schedule=self.schedule,
                status=CheckinStatus.PENDING,
            ).exists()
        )

    def test_technical_admin_home_does_not_render_dead_staff_links(self):
        user = get_user_model().objects.create_user(
            username="admin",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = user.pk
        session.save()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Acesso rápido", content)
        self.assertIn("quick-link--disabled", content)
        self.assertIn('href="/admin/"', content)
        self.assertNotIn('href="#"', content)

    def _login_portal_account(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def _today_weekday_code(self):
        return {
            0: WeekdayCode.MONDAY,
            1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY,
            3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY,
            5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }[timezone.localdate().weekday()]
