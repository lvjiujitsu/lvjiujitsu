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
    RegistrationOrder,
    SubscriptionPlan,
    TrainingStyle,
    TrialAccessGrant,
    WeekdayCode,
)
from system.models.calendar import (
    CheckinStatus,
    ClassCheckin,
    ClassSession,
    Holiday,
    SessionStatus,
    SpecialClass,
    SpecialClassCheckin,
)
from system.models import ClassInstructorAssignment
from system.models.category import CategoryAudience, ClassCategory
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY
from system.services.class_calendar import (
    approve_class_checkin,
    approve_special_checkin,
    assert_instructor_owns_schedule,
    assert_instructor_owns_special,
    create_special_class,
    delete_special_class,
    get_calendar_month_data,
    get_instructor_checkin_history,
    get_student_checkin_history,
    get_today_classes_for_instructor,
    get_today_classes_for_person,
    perform_checkin,
    perform_special_class_checkin,
    toggle_session_cancel,
)
from system.services.trial_access import grant_trial_for_order

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
        self.assertEqual(checkin.status, CheckinStatus.PENDING)
        self.assertIsNone(checkin.approved_at)
        self.assertIsNone(checkin.approved_by)

    def test_perform_checkin_idempotent(self):
        perform_checkin(self.person, self.schedule.pk)
        checkin, created = perform_checkin(self.person, self.schedule.pk)
        self.assertFalse(created)

    def test_trial_is_consumed_on_first_checkin_only(self):
        plan = SubscriptionPlan.objects.create(
            code="mensal-calendar-trial",
            display_name="Mensal Trial",
            price=100,
            billing_cycle="monthly",
            is_active=True,
        )
        order = RegistrationOrder.objects.create(
            person=self.person,
            plan=plan,
            plan_price=100,
            total=100,
        )
        grant_trial_for_order(order)

        perform_checkin(self.person, self.schedule.pk)
        grant = TrialAccessGrant.objects.get(order=order)
        self.assertEqual(grant.consumed_classes, 1)
        self.assertFalse(grant.is_active)

        perform_checkin(self.person, self.schedule.pk)
        grant.refresh_from_db()
        self.assertEqual(grant.consumed_classes, 1)

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


class CheckinApprovalServiceTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.category = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age", display_name="Adulto",
            audience=CategoryAudience.ADULT, minimum_age=18, maximum_age=99,
        )
        self.instructor = Person.objects.create(
            full_name="Prof. Aprovador", cpf="900.000.000-01",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.other_instructor = Person.objects.create(
            full_name="Prof. Externo", cpf="900.000.000-02",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.group = ClassGroup.objects.create(
            code="adult-approval", display_name="Turma Aprovação",
            class_category=self.category, main_teacher=self.instructor,
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
        self.student = Person.objects.create(
            full_name="Aluno Aprovação", cpf="900.000.000-03",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
        )
        ClassEnrollment.objects.create(
            class_group=self.group, person=self.student, status="active",
        )

    def test_approve_class_checkin_marks_as_approved(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        self.assertEqual(checkin.status, CheckinStatus.PENDING)

        approved = approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)

        self.assertEqual(approved.status, CheckinStatus.APPROVED)
        self.assertIsNotNone(approved.approved_at)
        self.assertEqual(approved.approved_by, self.instructor)

    def test_approve_class_checkin_idempotent(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)

        again = approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)
        self.assertEqual(again.status, CheckinStatus.APPROVED)

    def test_approve_class_checkin_blocks_unauthorized_instructor(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)

        with self.assertRaises(PermissionError):
            approve_class_checkin(instructor=self.other_instructor, checkin_id=checkin.pk)

        checkin.refresh_from_db()
        self.assertEqual(checkin.status, CheckinStatus.PENDING)

    def test_approve_class_checkin_authorizes_assigned_instructor(self):
        ClassInstructorAssignment.objects.create(
            class_group=self.group, person=self.other_instructor,
        )
        checkin, _ = perform_checkin(self.student, self.schedule.pk)

        approved = approve_class_checkin(
            instructor=self.other_instructor, checkin_id=checkin.pk
        )

        self.assertEqual(approved.status, CheckinStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.other_instructor)

    def test_get_today_classes_for_instructor_exposes_pending_and_approved(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]
        self.assertEqual(regular.checked_count, 1)
        self.assertEqual(regular.pending_count, 1)
        self.assertEqual(regular.approved_count, 0)
        self.assertEqual(regular.checkins[0].pk, checkin.pk)
        self.assertFalse(regular.checkins[0].is_approved)

        approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]
        self.assertEqual(regular.pending_count, 0)
        self.assertEqual(regular.approved_count, 1)
        self.assertTrue(regular.checkins[0].is_approved)

    def test_today_classes_for_instructor_exposes_quick_action_identifiers(self):
        special = create_special_class(
            title="Aulão rápido",
            date=timezone.localdate(),
            start_time=time(20, 0),
            teacher=self.instructor,
        )

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]
        special_entry = [e for e in entries if e.is_special][0]

        self.assertEqual(regular.schedule_id, self.schedule.pk)
        self.assertEqual(regular.session_date, timezone.localdate())
        self.assertFalse(regular.is_holiday_cancelled)
        self.assertEqual(special_entry.special_id, special.pk)

    def test_get_student_history_only_lists_approved(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        self.assertEqual(get_student_checkin_history(self.student), [])

        approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)

        history = get_student_checkin_history(self.student)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].group_name, "Turma Aprovação")

    def test_get_instructor_history_only_lists_approved(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        self.assertEqual(get_instructor_checkin_history(self.instructor), [])

        approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)

        history = get_instructor_checkin_history(self.instructor)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].attendees, ["Aluno Aprovação"])

    def test_today_classes_for_person_exposes_checkin_status(self):
        entries = get_today_classes_for_person(self.student)
        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].has_checked_in)
        self.assertFalse(entries[0].is_checkin_approved)

        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        entries = get_today_classes_for_person(self.student)
        self.assertTrue(entries[0].has_checked_in)
        self.assertFalse(entries[0].is_checkin_approved)
        self.assertEqual(entries[0].checkin_status, CheckinStatus.PENDING)

        approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)
        entries = get_today_classes_for_person(self.student)
        self.assertTrue(entries[0].is_checkin_approved)
        self.assertEqual(entries[0].checkin_status, CheckinStatus.APPROVED)


class InstructorScheduleOwnershipServiceTestCase(TestCase):
    def setUp(self):
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.category = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        self.instructor = Person.objects.create(
            full_name="Prof. Dono", cpf="910.000.000-01",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.outsider = Person.objects.create(
            full_name="Prof. Outro", cpf="910.000.000-02",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.group = ClassGroup.objects.create(
            code="group-ownership", display_name="Turma do Dono",
            class_category=self.category, main_teacher=self.instructor,
        )
        self.schedule = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=WeekdayCode.MONDAY,
            start_time=time(19, 0),
            training_style=TrainingStyle.GI,
        )

    def test_assert_instructor_owns_schedule_returns_schedule(self):
        result = assert_instructor_owns_schedule(self.instructor, self.schedule.pk)
        self.assertEqual(result.pk, self.schedule.pk)

    def test_assert_instructor_owns_schedule_blocks_outsider(self):
        with self.assertRaises(PermissionError):
            assert_instructor_owns_schedule(self.outsider, self.schedule.pk)

    def test_assert_instructor_owns_special_returns_special(self):
        special = create_special_class(
            title="Aulão Dono", date=timezone.localdate(),
            start_time=time(19, 0), teacher=self.instructor,
        )
        result = assert_instructor_owns_special(self.instructor, special.pk)
        self.assertEqual(result.pk, special.pk)

    def test_assert_instructor_owns_special_blocks_outsider(self):
        special = create_special_class(
            title="Aulão Dono", date=timezone.localdate(),
            start_time=time(19, 0), teacher=self.instructor,
        )
        with self.assertRaises(PermissionError):
            assert_instructor_owns_special(self.outsider, special.pk)


class SpecialCheckinApprovalServiceTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.teacher = Person.objects.create(
            full_name="Prof. Aulão", cpf="901.000.000-01",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.other_teacher = Person.objects.create(
            full_name="Prof. Outro", cpf="901.000.000-02",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.student = Person.objects.create(
            full_name="Aluno Aulão", cpf="901.000.000-03",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
        )

    def test_approve_special_checkin_marks_as_approved(self):
        special = create_special_class(
            title="Aulão Aprovação", date=timezone.localdate(),
            start_time=time(19, 0), teacher=self.teacher,
        )
        checkin, _ = perform_special_class_checkin(self.student, special.pk)
        self.assertEqual(checkin.status, CheckinStatus.PENDING)

        approved = approve_special_checkin(instructor=self.teacher, checkin_id=checkin.pk)
        self.assertEqual(approved.status, CheckinStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.teacher)

    def test_approve_special_checkin_blocks_unauthorized_instructor(self):
        special = create_special_class(
            title="Aulão Bloq", date=timezone.localdate(),
            start_time=time(19, 0), teacher=self.teacher,
        )
        checkin, _ = perform_special_class_checkin(self.student, special.pk)

        with self.assertRaises(PermissionError):
            approve_special_checkin(instructor=self.other_teacher, checkin_id=checkin.pk)


class InstructorHomeQuickActionsViewTestCase(TestCase):
    def setUp(self):
        self.instructor_type = PersonType.objects.create(
            code="instructor",
            display_name="Professor",
        )
        self.category = ClassCategory.objects.create(
            code="adult-home-actions",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
        )
        self.instructor = Person.objects.create(
            full_name="Professor Ações Rápidas",
            cpf="920.000.000-01",
            person_type=self.instructor_type,
            birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.account = PortalAccount(person=self.instructor)
        self.account.set_password("123456")
        self.account.save()
        self.group = ClassGroup.objects.create(
            code="adult-home-actions-group",
            display_name="Turma Ações",
            class_category=self.category,
            main_teacher=self.instructor,
        )

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def _today_weekday(self):
        weekday_map = {
            0: WeekdayCode.MONDAY,
            1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY,
            3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY,
            5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        return weekday_map[timezone.localdate().weekday()]

    def test_instructor_dashboard_exposes_quick_schedule_actions(self):
        schedule = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=self._today_weekday(),
            training_style=TrainingStyle.GI,
            start_time=time(19, 0),
            duration_minutes=60,
        )
        cancelled_schedule = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=self._today_weekday(),
            training_style=TrainingStyle.NO_GI,
            start_time=time(20, 0),
            duration_minutes=60,
        )
        ClassSession.objects.create(
            schedule=cancelled_schedule,
            date=timezone.localdate(),
            status=SessionStatus.CANCELLED,
            cancellation_reason="Ajuste de agenda",
        )
        self._login()

        response = self.client.get(reverse("system:instructor-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Criar aulão")
        self.assertContains(response, "data-quick-special-open")
        self.assertContains(response, "data-special-class-form")
        self.assertContains(response, "data-quick-cancel-session")
        self.assertContains(response, f'data-schedule-id="{schedule.pk}"')
        self.assertContains(response, "data-quick-reactivate-session")
        self.assertContains(response, f'data-schedule-id="{cancelled_schedule.pk}"')


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


class SpecialClassServiceTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.teacher = Person.objects.create(
            full_name="Prof. Teste", cpf="333.333.333-33",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.person = Person.objects.create(
            full_name="Aluno Aulao", cpf="444.444.444-44",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
        )

    def test_create_special_class(self):
        today = timezone.localdate()
        sc = create_special_class(
            title="Aulão Rei-Zulu",
            date=today,
            start_time=time(19, 0),
            duration_minutes=90,
            teacher=self.teacher,
            notes="Aberto a todos",
        )
        self.assertEqual(sc.title, "Aulão Rei-Zulu")
        self.assertEqual(sc.teacher, self.teacher)
        self.assertEqual(SpecialClass.objects.count(), 1)

    def test_create_special_class_on_holiday(self):
        today = timezone.localdate()
        Holiday.objects.create(date=today, name="Feriado")
        sc = create_special_class(
            title="Aulão feriado",
            date=today,
            start_time=time(10, 0),
        )
        self.assertEqual(sc.date, today)

    def test_delete_special_class(self):
        sc = create_special_class(
            title="Aulão",
            date=timezone.localdate(),
            start_time=time(19, 0),
        )
        delete_special_class(sc.pk)
        self.assertFalse(SpecialClass.objects.filter(pk=sc.pk).exists())

    def test_perform_special_class_checkin(self):
        sc = create_special_class(
            title="Aulão", date=timezone.localdate(), start_time=time(19, 0),
        )
        checkin, created = perform_special_class_checkin(self.person, sc.pk)
        self.assertTrue(created)
        self.assertEqual(checkin.person, self.person)

    def test_special_checkin_idempotent(self):
        sc = create_special_class(
            title="Aulão", date=timezone.localdate(), start_time=time(19, 0),
        )
        perform_special_class_checkin(self.person, sc.pk)
        _, created = perform_special_class_checkin(self.person, sc.pk)
        self.assertFalse(created)

    def test_special_checkin_blocked_on_other_date(self):
        sc = create_special_class(
            title="Aulão",
            date=timezone.localdate() + timezone.timedelta(days=3) if False else date(2099, 12, 31),
            start_time=time(19, 0),
        )
        with self.assertRaises(ValueError):
            perform_special_class_checkin(self.person, sc.pk)

    def test_today_classes_includes_special(self):
        create_special_class(
            title="Aulão", date=timezone.localdate(), start_time=time(20, 0),
        )
        entries = get_today_classes_for_person(self.person)
        specials = [e for e in entries if getattr(e, "is_special", False)]
        self.assertEqual(len(specials), 1)
        self.assertEqual(specials[0].group_name, "Aulão")
        self.assertFalse(specials[0].has_checked_in)

    def test_calendar_month_data_includes_specials(self):
        today = timezone.localdate()
        create_special_class(
            title="Aulão mês", date=today, start_time=time(19, 0),
        )
        data = get_calendar_month_data(today.year, today.month)
        day_entry = next(d for d in data.days if d.date == today)
        self.assertEqual(len(day_entry.specials), 1)
        self.assertEqual(day_entry.specials[0].group_name, "Aulão mês")


class SpecialClassViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin2", email="a2@test.com", password="admin",
        )
        self.admin_type = PersonType.objects.create(
            code="administrative-assistant", display_name="Administrativo",
        )
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.admin_person = Person.objects.create(
            full_name="Admin", cpf="555.555.555-55",
            person_type=self.admin_type, birth_date=date(1990, 1, 1),
            biological_sex="male",
        )
        self.admin_account = PortalAccount(person=self.admin_person)
        self.admin_account.set_password("123456")
        self.admin_account.save()
        self.student_person = Person.objects.create(
            full_name="Aluno", cpf="666.666.666-66",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
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

    def test_create_special_class_view(self):
        self._login_as_admin()
        today = timezone.localdate()
        response = self.client.post(
            reverse("system:admin-special-class-create"),
            data={
                "title": "Aulão X",
                "date": today.strftime("%Y-%m-%d"),
                "start_time": "19:00",
                "duration_minutes": 90,
                "notes": "",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SpecialClass.objects.filter(title="Aulão X").exists())

    def test_create_special_class_invalid(self):
        self._login_as_admin()
        response = self.client.post(
            reverse("system:admin-special-class-create"),
            data={"title": ""},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_special_class_view(self):
        self._login_as_admin()
        sc = SpecialClass.objects.create(
            title="Aulão Del", date=timezone.localdate(), start_time=time(19, 0),
        )
        response = self.client.post(
            reverse("system:admin-special-class-delete"),
            data={"special_id": sc.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SpecialClass.objects.filter(pk=sc.pk).exists())

    def test_student_special_checkin_view(self):
        self._login_as_student()
        sc = SpecialClass.objects.create(
            title="Aulão Check", date=timezone.localdate(), start_time=time(19, 0),
        )
        response = self.client.post(
            reverse("system:student-special-checkin"),
            data={"special_id": sc.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SpecialClassCheckin.objects.filter(
                special_class=sc, person=self.student_person
            ).exists()
        )
