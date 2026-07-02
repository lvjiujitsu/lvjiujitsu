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
    assign_session_substitute,
    assign_special_substitute,
    cancel_class_without_instructor,
    cancel_instructor_self_checkin,
    cancel_instructor_self_special_checkin,
    cancel_special_without_instructor,
    create_special_class,
    delete_special_class,
    get_calendar_month_data,
    get_instructor_checkin_history,
    get_student_checkin_history,
    get_today_classes_for_administrative,
    get_today_classes_for_instructor,
    get_today_classes_for_person,
    perform_checkin,
    perform_special_class_checkin,
    register_instructor_self_checkin,
    register_instructor_self_special_checkin,
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
            display_name="Teste", class_category=self.category,
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
            display_name="Turma Teste", class_category=self.category,
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
            code="monthly-trial",
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

    def test_calendar_page_renders_responsive_day_detail_contract(self):
        self._login_portal_account(self.account)

        response = self.client.get(reverse("system:calendar"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('class="page page--calendar"', content)
        self.assertIn("calendar-board", content)
        self.assertIn('class="cal-grid cal-grid--days"', content)
        self.assertIn('class="cal-day__button js-open-day-detail"', content)
        self.assertIn('id="calendar-day-modal"', content)
        self.assertIn('id="calendar-day-modal-body"', content)

    def test_student_entry_has_instructor_present_true_when_no_session(self):
        classes = get_today_classes_for_person(self.person)
        self.assertEqual(len(classes), 1)
        self.assertTrue(classes[0].instructor_present)

    def test_student_entry_has_instructor_present_false_when_not_checked_in(self):
        today = timezone.localdate()
        ClassSession.objects.create(
            schedule=self.schedule, date=today,
            status=SessionStatus.SCHEDULED, instructor_present=False,
        )
        classes = get_today_classes_for_person(self.person)
        self.assertFalse(classes[0].instructor_present)

    def test_student_entry_has_instructor_present_true_when_instructor_checked_in(self):
        from django.utils import timezone as tz
        today = timezone.localdate()
        ClassSession.objects.create(
            schedule=self.schedule, date=today,
            status=SessionStatus.SCHEDULED, instructor_present=True,
            instructor_checked_in_at=tz.now(),
        )
        classes = get_today_classes_for_person(self.person)
        self.assertTrue(classes[0].instructor_present)

    def test_special_class_student_entry_has_instructor_present(self):
        special = SpecialClass.objects.create(
            title="Aulão Teste", date=timezone.localdate(),
            start_time=time(10, 0), instructor_present=True,
        )
        classes = get_today_classes_for_person(self.person)
        special_entries = [c for c in classes if c.is_special]
        self.assertEqual(len(special_entries), 1)
        self.assertTrue(special_entries[0].instructor_present)
        special.instructor_present = False
        special.save()
        classes = get_today_classes_for_person(self.person)
        special_entries = [c for c in classes if c.is_special]
        self.assertFalse(special_entries[0].instructor_present)

    def _login_portal_account(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()


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
            display_name="Turma Aprovação",
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

    def test_approve_class_checkin_blocks_cancelled_session(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        checkin.session.status = SessionStatus.CANCELLED
        checkin.session.save(update_fields=["status"])

        with self.assertRaises(ValueError):
            approve_class_checkin(instructor=self.instructor, checkin_id=checkin.pk)

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

    def test_get_instructor_history_reflects_own_self_checkin(self):
        self.assertEqual(get_instructor_checkin_history(self.instructor), [])

        register_instructor_self_checkin(self.instructor, self.schedule.pk)

        history = get_instructor_checkin_history(self.instructor)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].group_name, "Turma Aprovação")
        self.assertFalse(history[0].is_special)

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


class InstructorApproveCheckinViewTestCase(TestCase):
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
            full_name="Prof. View Aprovador", cpf="900.000.000-11",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.group = ClassGroup.objects.create(
            display_name="Turma View Aprovação",
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
            full_name="Aluno View Aprovação", cpf="900.000.000-12",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
        )
        ClassEnrollment.objects.create(
            class_group=self.group, person=self.student, status="active",
        )
        account = PortalAccount(person=self.instructor)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_approve_checkin_of_cancelled_session_returns_clean_400(self):
        checkin, _ = perform_checkin(self.student, self.schedule.pk)
        checkin.session.status = SessionStatus.CANCELLED
        checkin.session.save(update_fields=["status"])

        response = self.client.post(
            reverse("system:instructor-approve-checkin"),
            data=json.dumps({"checkin_id": checkin.pk}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("cancelada", response.json()["error"])
        checkin.refresh_from_db()
        self.assertEqual(checkin.status, CheckinStatus.PENDING)


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
            display_name="Turma do Dono",
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

    def test_calendar_month_data_does_not_crash_when_special_falls_on_holiday(self):
        today = timezone.localdate()
        Holiday.objects.create(date=today, name="Feriado Aulão Fundacao")
        create_special_class(
            title="Aulão em feriado", date=today, start_time=time(19, 0),
        )

        data = get_calendar_month_data(today.year, today.month)

        day_entry = next(d for d in data.days if d.date == today)
        self.assertTrue(day_entry.specials[0].is_cancelled)
        self.assertEqual(day_entry.specials[0].cancellation_reason, "Feriado Aulão Fundacao")


class InstructorSelfCheckinServiceTestCase(TestCase):
    def setUp(self):
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.category = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age", display_name="Adulto",
            audience=CategoryAudience.ADULT, minimum_age=18, maximum_age=99,
        )
        self.instructor = Person.objects.create(
            full_name="Prof. Self", cpf="950.000.000-01",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.other_instructor = Person.objects.create(
            full_name="Prof. Outro", cpf="950.000.000-02",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        self.group = ClassGroup.objects.create(
            display_name="Turma Self", class_category=self.category,
            main_teacher=self.instructor,
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
        self.instructor_account = PortalAccount(person=self.instructor)
        self.instructor_account.set_password("123456")
        self.instructor_account.save()

    def test_self_checkin_registers_presence(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)

        session, created = register_instructor_self_checkin(self.instructor, self.schedule.pk)
        self.assertTrue(created)
        self.assertTrue(session.instructor_present)
        self.assertIsNotNone(session.instructor_checked_in_at)

    def test_self_checkin_creates_session_if_not_exists(self):
        self.assertFalse(ClassSession.objects.filter(schedule=self.schedule).exists())
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        register_instructor_self_checkin(self.instructor, self.schedule.pk)
        self.assertTrue(ClassSession.objects.filter(schedule=self.schedule).exists())

    def test_self_checkin_idempotent(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        register_instructor_self_checkin(self.instructor, self.schedule.pk)
        _, created = register_instructor_self_checkin(self.instructor, self.schedule.pk)
        self.assertFalse(created)
        self.assertEqual(ClassSession.objects.filter(schedule=self.schedule).count(), 1)

    def test_self_checkin_blocks_other_instructor(self):
        with self.assertRaises(PermissionError):
            register_instructor_self_checkin(self.other_instructor, self.schedule.pk)

    def test_self_checkin_blocked_on_cancelled_session(self):
        today = timezone.localdate()
        toggle_session_cancel(self.schedule.pk, today, "Motivo")
        with self.assertRaises(ValueError):
            register_instructor_self_checkin(self.instructor, self.schedule.pk)

    def test_self_checkin_cancel_clears_presence(self):
        session, changed = cancel_instructor_self_checkin(
            self.instructor,
            self.schedule.pk,
        )

        self.assertTrue(changed)
        self.assertFalse(session.instructor_present)
        self.assertIsNone(session.instructor_checked_in_at)

    def test_assign_session_substitute_requires_cancelled_confirmation(self):
        with self.assertRaises(ValueError):
            assign_session_substitute(
                self.instructor,
                self.schedule.pk,
                self.other_instructor.pk,
            )

    def test_assign_session_substitute_clears_original_presence(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)

        session = assign_session_substitute(
            self.instructor,
            self.schedule.pk,
            self.other_instructor.pk,
        )

        self.assertEqual(session.substitute_teacher, self.other_instructor)
        self.assertFalse(session.instructor_present)
        self.assertIsNone(session.instructor_checked_in_at)

    def test_substitute_instructor_sees_regular_class(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        assign_session_substitute(
            self.instructor,
            self.schedule.pk,
            self.other_instructor.pk,
        )

        entries = get_today_classes_for_instructor(self.other_instructor)

        self.assertEqual(len([entry for entry in entries if not entry.is_special]), 1)
        regular = [entry for entry in entries if not entry.is_special][0]
        self.assertEqual(regular.schedule_id, self.schedule.pk)
        self.assertTrue(regular.is_substitute_assignment)
        self.assertEqual(regular.substitute_teacher_name, self.other_instructor.full_name)

    def test_substitute_instructor_can_register_presence(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        assign_session_substitute(
            self.instructor,
            self.schedule.pk,
            self.other_instructor.pk,
        )

        session, created = register_instructor_self_checkin(
            self.other_instructor,
            self.schedule.pk,
        )

        self.assertTrue(created)
        self.assertTrue(session.instructor_present)
        self.assertEqual(session.substitute_teacher, self.other_instructor)

    def test_substitute_confirmed_shows_green_for_original_instructor(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        assign_session_substitute(
            self.instructor,
            self.schedule.pk,
            self.other_instructor.pk,
        )
        register_instructor_self_checkin(self.other_instructor, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]

        self.assertTrue(regular.instructor_present)
        self.assertTrue(regular.substitute_confirmed)
        self.assertFalse(regular.can_assign_substitute)

    def test_substitute_cancel_releases_class_to_original_instructor(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        assign_session_substitute(
            self.instructor,
            self.schedule.pk,
            self.other_instructor.pk,
        )
        register_instructor_self_checkin(self.other_instructor, self.schedule.pk)
        cancel_instructor_self_checkin(self.other_instructor, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]

        self.assertFalse(regular.instructor_present)
        self.assertTrue(regular.can_confirm_presence)
        self.assertTrue(regular.can_assign_substitute)
        self.assertTrue(regular.can_cancel_class)
        self.assertEqual(regular.substitute_teacher_name, "")

    def test_cancel_class_without_instructor_toggles_cancel_and_restore(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)

        session = cancel_class_without_instructor(self.instructor, self.schedule.pk)
        self.assertTrue(session.is_cancelled)

        session = cancel_class_without_instructor(self.instructor, self.schedule.pk)
        self.assertFalse(session.is_cancelled)

    def test_today_classes_exposes_can_uncancel_class_after_instructor_cancel(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        cancel_class_without_instructor(self.instructor, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [entry for entry in entries if not entry.is_special][0]

        self.assertTrue(regular.is_cancelled)
        self.assertTrue(regular.can_uncancel_class)

        cancel_class_without_instructor(self.instructor, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [entry for entry in entries if not entry.is_special][0]

        self.assertFalse(regular.is_cancelled)
        self.assertFalse(regular.can_uncancel_class)
        self.assertTrue(regular.can_confirm_presence)

    def test_instructor_cancel_class_today_view_restores_cancelled_class(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        cancel_class_without_instructor(self.instructor, self.schedule.pk)

        self._login_portal_account(self.instructor_account)
        response = self.client.post(
            reverse("system:instructor-cancel-class-today"),
            data='{"schedule_id": %d}' % self.schedule.pk,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertFalse(payload["is_cancelled"])

    def test_cancel_special_without_instructor_toggles_cancel_and_restore(self):
        special = create_special_class(
            title="Aulão Toggle", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)

        special = cancel_special_without_instructor(self.instructor, special.pk)
        self.assertTrue(special.is_cancelled)

        special = cancel_special_without_instructor(self.instructor, special.pk)
        self.assertFalse(special.is_cancelled)

    def test_today_classes_exposes_special_cancel_and_restore_controls(self):
        special = create_special_class(
            title="Aulão Home", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        cancel_special_without_instructor(self.instructor, special.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        special_entry = [entry for entry in entries if entry.is_special][0]

        self.assertTrue(special_entry.is_cancelled)
        self.assertTrue(special_entry.can_uncancel_class)

        cancel_special_without_instructor(self.instructor, special.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        special_entry = [entry for entry in entries if entry.is_special][0]

        self.assertFalse(special_entry.is_cancelled)
        self.assertTrue(special_entry.can_confirm_presence)
        self.assertTrue(special_entry.can_cancel_class)

    def test_instructor_cancel_special_today_view_restores_cancelled_special(self):
        special = create_special_class(
            title="Aulão API", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        cancel_special_without_instructor(self.instructor, special.pk)

        self._login_portal_account(self.instructor_account)
        response = self.client.post(
            reverse("system:instructor-cancel-class-today"),
            data='{"special_id": %d}' % special.pk,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertFalse(payload["is_cancelled"])

    def test_assign_session_substitute_rejects_self(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        with self.assertRaises(ValueError):
            assign_session_substitute(
                self.instructor,
                self.schedule.pk,
                self.instructor.pk,
            )

    def test_today_classes_for_instructor_exposes_instructor_present(self):
        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]
        self.assertTrue(regular.instructor_present)
        self.assertIsNone(regular.instructor_checked_in_at)
        self.assertTrue(regular.can_cancel_presence)
        self.assertFalse(regular.can_assign_substitute)

        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]
        self.assertFalse(regular.instructor_present)
        self.assertTrue(regular.can_assign_substitute)
        self.assertTrue(regular.can_confirm_presence)

        register_instructor_self_checkin(self.instructor, self.schedule.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        regular = [e for e in entries if not e.is_special][0]
        self.assertTrue(regular.instructor_present)
        self.assertIsNotNone(regular.instructor_checked_in_at)

    def test_self_special_checkin_registers_presence(self):
        special = create_special_class(
            title="Aulão Self", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)

        result, created = register_instructor_self_special_checkin(self.instructor, special.pk)
        self.assertTrue(created)
        self.assertTrue(result.instructor_present)
        self.assertIsNotNone(result.instructor_checked_in_at)

    def test_self_special_checkin_blocks_other_instructor(self):
        special = create_special_class(
            title="Aulão Self", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        with self.assertRaises(PermissionError):
            register_instructor_self_special_checkin(self.other_instructor, special.pk)

    def test_self_special_checkin_blocked_on_wrong_date(self):
        special = create_special_class(
            title="Aulão Futuro", date=date(2099, 12, 31),
            start_time=time(20, 0), teacher=self.instructor,
        )
        with self.assertRaises(ValueError):
            register_instructor_self_special_checkin(self.instructor, special.pk)

    def test_self_special_checkin_cancel_clears_presence(self):
        special = create_special_class(
            title="Aulão Self", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        register_instructor_self_special_checkin(self.instructor, special.pk)

        special, changed = cancel_instructor_self_special_checkin(
            self.instructor,
            special.pk,
        )

        self.assertTrue(changed)
        self.assertFalse(special.instructor_present)
        self.assertIsNone(special.instructor_checked_in_at)

    def test_instructor_history_shows_own_checkins(self):
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        register_instructor_self_checkin(self.instructor, self.schedule.pk)
        history = get_instructor_checkin_history(self.instructor)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].group_name, "Turma Self")
        self.assertFalse(history[0].is_special)

    def test_instructor_history_shows_aulao_presence(self):
        special = create_special_class(
            title="Aulão History", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        register_instructor_self_special_checkin(self.instructor, special.pk)
        history = get_instructor_checkin_history(self.instructor)
        specials = [e for e in history if e.is_special]
        self.assertEqual(len(specials), 1)
        self.assertEqual(specials[0].group_name, "Aulão History")

    def test_instructor_history_empty_without_self_checkin(self):
        history = get_instructor_checkin_history(self.instructor)
        self.assertEqual(history, [])

    def test_assign_special_substitute_requires_cancelled_confirmation(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        register_instructor_self_special_checkin(self.instructor, special.pk)
        with self.assertRaises(ValueError):
            assign_special_substitute(
                self.instructor,
                special.pk,
                self.other_instructor.pk,
            )

    def test_assign_special_substitute_clears_original_presence(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)

        special = assign_special_substitute(
            self.instructor,
            special.pk,
            self.other_instructor.pk,
        )

        self.assertEqual(special.substitute_teacher, self.other_instructor)
        self.assertFalse(special.instructor_present)
        self.assertIsNone(special.instructor_checked_in_at)

    def test_substitute_instructor_sees_special_class(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        assign_special_substitute(
            self.instructor,
            special.pk,
            self.other_instructor.pk,
        )

        entries = get_today_classes_for_instructor(self.other_instructor)
        specials = [entry for entry in entries if entry.is_special]

        self.assertEqual(len(specials), 1)
        self.assertEqual(specials[0].special_id, special.pk)
        self.assertTrue(specials[0].is_substitute_assignment)
        self.assertEqual(specials[0].substitute_teacher_name, self.other_instructor.full_name)

    def test_substitute_instructor_can_register_special_presence(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        assign_special_substitute(
            self.instructor,
            special.pk,
            self.other_instructor.pk,
        )

        result, created = register_instructor_self_special_checkin(
            self.other_instructor,
            special.pk,
        )

        self.assertTrue(created)
        self.assertTrue(result.instructor_present)
        self.assertEqual(result.substitute_teacher, self.other_instructor)

    def test_special_substitute_confirmed_shows_green_for_original_instructor(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        assign_special_substitute(
            self.instructor,
            special.pk,
            self.other_instructor.pk,
        )
        register_instructor_self_special_checkin(self.other_instructor, special.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        special_entry = [e for e in entries if e.is_special][0]

        self.assertTrue(special_entry.instructor_present)
        self.assertTrue(special_entry.substitute_confirmed)
        self.assertFalse(special_entry.can_assign_substitute)

    def test_special_substitute_cancel_releases_to_original_instructor(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        assign_special_substitute(
            self.instructor,
            special.pk,
            self.other_instructor.pk,
        )
        register_instructor_self_special_checkin(self.other_instructor, special.pk)
        cancel_instructor_self_special_checkin(self.other_instructor, special.pk)

        entries = get_today_classes_for_instructor(self.instructor)
        special_entry = [e for e in entries if e.is_special][0]

        self.assertFalse(special_entry.instructor_present)
        self.assertTrue(special_entry.can_confirm_presence)
        self.assertTrue(special_entry.can_assign_substitute)
        self.assertTrue(special_entry.can_cancel_class)
        self.assertEqual(special_entry.substitute_teacher_name, "")

    def test_cancel_special_blocked_when_substitute_assigned(self):
        special = create_special_class(
            title="Aulão Sub", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.instructor,
        )
        cancel_instructor_self_special_checkin(self.instructor, special.pk)
        assign_special_substitute(
            self.instructor,
            special.pk,
            self.other_instructor.pk,
        )
        with self.assertRaises(ValueError):
            cancel_special_without_instructor(self.instructor, special.pk)

    def _login_portal_account(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_self_checkin_view_returns_success(self):
        self._login_portal_account(self.instructor_account)
        import json
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        response = self.client.post(
            reverse("system:instructor-self-checkin"),
            data=json.dumps({"schedule_id": self.schedule.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["created"])

    def test_self_checkin_view_idempotent(self):
        self._login_portal_account(self.instructor_account)
        import json
        response = self.client.post(
            reverse("system:instructor-self-checkin"),
            data=json.dumps({"schedule_id": self.schedule.pk}),
            content_type="application/json",
        )
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["created"])

    def test_self_checkin_cancel_view_returns_success(self):
        self._login_portal_account(self.instructor_account)
        import json

        response = self.client.post(
            reverse("system:instructor-self-checkin-cancel"),
            data=json.dumps({"schedule_id": self.schedule.pk}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["changed"])

    def test_session_substitute_view_returns_success(self):
        self._login_portal_account(self.instructor_account)
        import json
        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)

        response = self.client.post(
            reverse("system:instructor-session-substitute"),
            data=json.dumps({
                "schedule_id": self.schedule.pk,
                "substitute_teacher_id": self.other_instructor.pk,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["substitute_teacher_name"], self.other_instructor.full_name)

    def test_instructor_home_renders_presence_management_controls(self):
        self._login_portal_account(self.instructor_account)

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("js-instructor-self-checkin-cancel", content)
        self.assertNotIn('class="btn btn--outline presence-action js-open-substitute-modal"', content)
        self.assertIn("substitute-teacher-modal", content)
        self.assertIn("instructorSessionSubstituteUrl", content)
        self.assertIn("Confirmado", content)
        self.assertIn("section-action__icon", content)
        self.assertIn("presence-chip__dismiss-icon", content)

        cancel_instructor_self_checkin(self.instructor, self.schedule.pk)
        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")
        self.assertIn('class="btn btn--outline presence-action js-open-substitute-modal"', content)
        self.assertIn("presence-action__icon", content)

        cancel_class_without_instructor(self.instructor, self.schedule.pk)
        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")
        self.assertIn("js-instructor-restore-class", content)
        self.assertIn("Aula cancelada", content)


class AdministrativeProfileTestCase(TestCase):
    def setUp(self):
        self.admin_type = PersonType.objects.create(code="administrative-assistant", display_name="Administrativo")
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.category = ClassCategory.objects.create(
            code="kids", display_name="Kids", audience=CategoryAudience.KIDS,
        )
        self.category_adult = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="kids-age", display_name="Kids",
            audience=CategoryAudience.KIDS, minimum_age=4, maximum_age=12,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age", display_name="Adulto",
            audience=CategoryAudience.ADULT, minimum_age=18, maximum_age=99,
        )
        self.teacher = Person.objects.create(
            full_name="Prof. Principal", cpf="920.000.002-01",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        today = timezone.localdate()
        weekday_map = {
            0: WeekdayCode.MONDAY, 1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY, 3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY, 5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        self.kids_group = ClassGroup.objects.create(
            display_name="Kids", class_category=self.category, main_teacher=self.teacher,
        )
        self.adult_group = ClassGroup.objects.create(
            display_name="Adulto", class_category=self.category_adult, main_teacher=self.teacher,
        )
        self.kids_schedule = ClassSchedule.objects.create(
            class_group=self.kids_group,
            weekday=weekday_map[today.weekday()],
            start_time=time(10, 0),
            training_style=TrainingStyle.GI,
        )
        self.adult_schedule = ClassSchedule.objects.create(
            class_group=self.adult_group,
            weekday=weekday_map[today.weekday()],
            start_time=time(19, 0),
            training_style=TrainingStyle.GI,
        )
        self.administrative = Person.objects.create(
            full_name="Aline Admin", cpf="920.000.011-81",
            person_type=self.admin_type, birth_date=date(1995, 1, 1),
            biological_sex="female",
            class_group=self.adult_group,
        )
        ClassInstructorAssignment.objects.create(
            class_group=self.kids_group, person=self.administrative,
        )

    def test_managed_class_appears_as_instructor_entry(self):
        entries = get_today_classes_for_administrative(self.administrative)
        kids_entries = [e for e in entries if e.group_name == "Kids"]
        self.assertEqual(len(kids_entries), 1)
        self.assertEqual(kids_entries[0].entry_role, "instructor")

    def test_enrolled_class_appears_as_student_entry(self):
        entries = get_today_classes_for_administrative(self.administrative)
        adult_entries = [e for e in entries if e.group_name == "Adulto"]
        self.assertEqual(len(adult_entries), 1)
        self.assertEqual(adult_entries[0].entry_role, "student")

    def test_enrolled_class_not_duplicated_as_instructor(self):
        entries = get_today_classes_for_administrative(self.administrative)
        adult_entries = [e for e in entries if e.group_name == "Adulto"]
        self.assertEqual(len(adult_entries), 1)

    def test_student_entry_exposes_checkin_fields(self):
        entries = get_today_classes_for_administrative(self.administrative)
        adult = next(e for e in entries if e.group_name == "Adulto")
        self.assertFalse(adult.has_checked_in)
        self.assertFalse(adult.is_checkin_approved)

        perform_checkin(self.administrative, self.adult_schedule.pk)
        entries = get_today_classes_for_administrative(self.administrative)
        adult = next(e for e in entries if e.group_name == "Adulto")
        self.assertTrue(adult.has_checked_in)

    def test_get_today_classes_for_person_uses_active_enrollments_for_administrative_student(self):
        layon = Person.objects.create(
            full_name="Layon Prof", cpf="920.000.010-01",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex="male",
        )
        morning_group = ClassGroup.objects.create(
            display_name="Adulto Manhã", class_category=self.category_adult, main_teacher=layon,
        )
        ClassSchedule.objects.create(
            class_group=morning_group,
            weekday=self.adult_schedule.weekday,
            start_time=time(6, 30),
            training_style=TrainingStyle.GI,
        )
        self.administrative.jiu_jitsu_belt = "purple"
        self.administrative.save(update_fields=["jiu_jitsu_belt", "updated_at"])
        ClassEnrollment.objects.create(
            class_group=morning_group,
            person=self.administrative,
            status="active",
        )

        entries = get_today_classes_for_person(self.administrative)
        regular_entries = [entry for entry in entries if not entry.is_special]
        start_times = {entry.start_time for entry in regular_entries}

        self.assertIn("06:30", start_times)
        self.assertIn("19:00", start_times)

    def test_instructor_entry_exposes_approval_fields(self):
        student = Person.objects.create(
            full_name="Aluno Kids", cpf="920.000.003-01",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex="male",
        )
        perform_checkin(student, self.kids_schedule.pk)

        entries = get_today_classes_for_administrative(self.administrative)
        kids = next(e for e in entries if e.group_name == "Kids")
        self.assertEqual(kids.entry_role, "instructor")
        self.assertEqual(kids.checked_count, 1)
        self.assertEqual(kids.pending_count, 1)

    def test_aulaon_where_teacher_appears_as_instructor(self):
        special = create_special_class(
            title="Aulão Admin", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.administrative,
        )
        entries = get_today_classes_for_administrative(self.administrative)
        sp = next(e for e in entries if e.special_id == special.pk)
        self.assertEqual(sp.entry_role, "instructor")

    def test_aulaon_where_not_teacher_appears_as_student(self):
        special = create_special_class(
            title="Aulão Externo", date=timezone.localdate(),
            start_time=time(20, 0), teacher=self.teacher,
        )
        entries = get_today_classes_for_administrative(self.administrative)
        sp = next(e for e in entries if e.special_id == special.pk)
        self.assertEqual(sp.entry_role, "student")
        self.assertFalse(sp.has_checked_in)

    def test_no_managed_groups_returns_student_and_aulao_entries(self):
        admin2 = Person.objects.create(
            full_name="Admin Dois", cpf="920.000.004-01",
            person_type=self.admin_type, birth_date=date(1995, 1, 1),
            biological_sex="female",
            class_group=self.adult_group,
        )
        create_special_class(title="Aulão Geral", date=timezone.localdate(), start_time=time(20, 0))
        entries = get_today_classes_for_administrative(admin2)
        adult_entries = [e for e in entries if e.group_name == "Adulto"]
        aulaon_entries = [e for e in entries if e.group_name == "Aulão Geral"]
        self.assertEqual(len(adult_entries), 1)
        self.assertEqual(adult_entries[0].entry_role, "student")
        self.assertEqual(len(aulaon_entries), 1)
        self.assertEqual(aulaon_entries[0].entry_role, "student")
