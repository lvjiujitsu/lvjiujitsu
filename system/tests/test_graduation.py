from datetime import date, time, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from system.models import (
    BeltRank,
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassSchedule,
    ClassSession,
    Graduation,
    GraduationRule,
    IbjjfAgeCategory,
    Person,
    PersonType,
    PortalAccount,
    TrainingStyle,
    WeekdayCode,
)
from system.models.calendar import CheckinStatus, ClassCheckin
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY
from system.services.graduation import (
    compute_graduation_progress,
    count_approved_classes_in_window,
    get_current_graduation,
    register_graduation,
)
from system.selectors.graduation import get_graduation_overview


User = get_user_model()


class BeltRankModelTestCase(TestCase):
    def test_unique_code(self):
        BeltRank.objects.create(
            code="adult-white", display_name="Branca",
            audience=CategoryAudience.ADULT, color_hex="#fff",
            max_grades=4, display_order=10,
        )
        with self.assertRaises(Exception):
            BeltRank.objects.create(
                code="adult-white", display_name="Branca duplicada",
                audience=CategoryAudience.ADULT, color_hex="#fff",
                max_grades=4, display_order=11,
            )

    def test_next_rank_relationship(self):
        white = BeltRank.objects.create(
            code="adult-white", display_name="Branca",
            audience=CategoryAudience.ADULT, color_hex="#fff",
            max_grades=4, display_order=10,
        )
        blue = BeltRank.objects.create(
            code="adult-blue", display_name="Azul",
            audience=CategoryAudience.ADULT, color_hex="#00f",
            max_grades=4, display_order=20,
        )
        white.next_rank = blue
        white.save()
        self.assertEqual(white.next_rank, blue)

    def test_get_grade_slots_marks_filled_positions(self):
        belt = BeltRank.objects.create(
            code="adult-white-slots", display_name="Branca",
            audience=CategoryAudience.ADULT, color_hex="#fff",
            tip_color_hex="#000000", stripe_color_hex="#ffffff",
            max_grades=4, display_order=10,
        )
        self.assertEqual(belt.get_grade_slots(0), [False, False, False, False])
        self.assertEqual(belt.get_grade_slots(2), [True, True, False, False])
        self.assertEqual(belt.get_grade_slots(4), [True, True, True, True])
        self.assertEqual(belt.get_grade_slots(99), [True, True, True, True])

    def test_get_grade_slots_returns_empty_when_no_grades(self):
        belt = BeltRank.objects.create(
            code="adult-coral", display_name="Coral",
            audience=CategoryAudience.ADULT, color_hex="#dc2626",
            max_grades=0, display_order=200,
        )
        self.assertEqual(belt.get_grade_slots(2), [])

    def test_default_tip_and_stripe_colors(self):
        belt = BeltRank.objects.create(
            code="adult-default-colors", display_name="Padrão",
            audience=CategoryAudience.ADULT, color_hex="#0ea5e9",
            max_grades=4, display_order=15,
        )
        self.assertEqual(belt.tip_color_hex, "#000000")
        self.assertEqual(belt.stripe_color_hex, "#ffffff")


class GraduationServiceTestCase(TestCase):
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
        self.white = BeltRank.objects.create(
            code="adult-white", display_name="Branca",
            audience=CategoryAudience.ADULT, color_hex="#fff",
            max_grades=4, display_order=10,
        )
        self.blue = BeltRank.objects.create(
            code="adult-blue", display_name="Azul",
            audience=CategoryAudience.ADULT, color_hex="#2563eb",
            max_grades=4, display_order=20,
        )
        self.white.next_rank = self.blue
        self.white.save()
        GraduationRule.objects.create(
            belt_rank=self.white, from_grade=0, to_grade=1,
            min_months_in_current_grade=4, min_classes_required=2,
            min_classes_window_months=12, is_active=True,
        )
        self.person = Person.objects.create(
            full_name="Aluno Faixa", cpf="800.000.000-01",
            person_type=self.student_type, birth_date=date(2000, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.instructor = Person.objects.create(
            full_name="Prof.", cpf="800.000.000-02",
            person_type=self.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.group = ClassGroup.objects.create(
            display_name="Turma",
            class_category=self.category, main_teacher=self.instructor,
        )
        ClassEnrollment.objects.create(
            class_group=self.group, person=self.person, status="active",
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

    def _create_approved_checkin(self, days_back):
        target_date = timezone.localdate() - timedelta(days=days_back)
        session, _ = ClassSession.objects.get_or_create(
            schedule=self.schedule,
            date=target_date,
        )
        return ClassCheckin.objects.create(
            session=session,
            person=self.person,
            status=CheckinStatus.APPROVED,
        )

    def test_register_graduation_creates_record(self):
        graduation = register_graduation(
            person=self.person,
            belt_rank=self.white,
            grade_number=0,
            awarded_by=self.instructor,
            awarded_at=timezone.localdate() - timedelta(days=180),
        )
        self.assertEqual(graduation.person, self.person)
        self.assertEqual(graduation.belt_rank, self.white)
        self.assertEqual(get_current_graduation(self.person), graduation)

    def test_register_graduation_blocks_grade_above_max(self):
        with self.assertRaises(ValueError):
            register_graduation(
                person=self.person,
                belt_rank=self.white,
                grade_number=99,
            )

    def test_count_approved_classes_in_window(self):
        self._create_approved_checkin(days_back=10)
        self._create_approved_checkin(days_back=400)
        start = timezone.localdate() - timedelta(days=365)
        end = timezone.localdate()
        self.assertEqual(count_approved_classes_in_window(self.person, start, end), 1)

    def test_count_approved_classes_same_day_counts_once(self):
        # Two check-ins on the same day must count as 1 unique training day.
        target_date = timezone.localdate() - timedelta(days=5)
        session1, _ = ClassSession.objects.get_or_create(schedule=self.schedule, date=target_date)
        ClassCheckin.objects.create(session=session1, person=self.person, status=CheckinStatus.APPROVED)
        schedule2 = ClassSchedule.objects.create(
            class_group=self.group,
            weekday=self.schedule.weekday,
            start_time=__import__("datetime").time(21, 0),
            training_style=TrainingStyle.GI,
        )
        session2, _ = ClassSession.objects.get_or_create(schedule=schedule2, date=target_date)
        ClassCheckin.objects.create(session=session2, person=self.person, status=CheckinStatus.APPROVED)
        start = timezone.localdate() - timedelta(days=30)
        end = timezone.localdate()
        self.assertEqual(count_approved_classes_in_window(self.person, start, end), 1)

    def test_count_approved_classes_different_days_count_separately(self):
        self._create_approved_checkin(days_back=5)
        self._create_approved_checkin(days_back=15)
        self._create_approved_checkin(days_back=25)
        start = timezone.localdate() - timedelta(days=30)
        end = timezone.localdate()
        self.assertEqual(count_approved_classes_in_window(self.person, start, end), 3)

    def test_compute_progress_with_pending_requirements(self):
        register_graduation(
            person=self.person, belt_rank=self.white, grade_number=0,
            awarded_at=timezone.localdate() - timedelta(days=30),
        )
        progress = compute_graduation_progress(self.person)
        self.assertEqual(progress.current_belt_rank, self.white)
        self.assertEqual(progress.current_grade_number, 0)
        self.assertGreater(progress.required_months, progress.months_in_current_grade)
        self.assertFalse(progress.is_eligible)

    def test_compute_progress_eligible_when_requirements_met(self):
        register_graduation(
            person=self.person, belt_rank=self.white, grade_number=0,
            awarded_at=timezone.localdate() - timedelta(days=200),
        )
        self._create_approved_checkin(days_back=10)
        self._create_approved_checkin(days_back=20)
        progress = compute_graduation_progress(self.person)
        self.assertTrue(progress.is_eligible)
        self.assertEqual(progress.target_belt_rank, self.white)
        self.assertEqual(progress.target_grade_number, 1)

    def test_compute_progress_targets_next_rank_when_rule_promotes(self):
        GraduationRule.objects.create(
            belt_rank=self.white, from_grade=4, to_grade=None,
            min_months_in_current_grade=0, min_classes_required=0,
            min_classes_window_months=0, is_active=True,
        )
        register_graduation(
            person=self.person, belt_rank=self.white, grade_number=4,
            awarded_at=timezone.localdate() - timedelta(days=10),
        )
        progress = compute_graduation_progress(self.person)
        self.assertEqual(progress.target_belt_rank, self.blue)
        self.assertEqual(progress.target_grade_number, 0)

    def test_overview_includes_active_students(self):
        register_graduation(
            person=self.person, belt_rank=self.white, grade_number=0,
            awarded_at=timezone.localdate() - timedelta(days=30),
        )
        rows = get_graduation_overview()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].person, self.person)


class InitialTeacherSeedGraduationTestCase(TestCase):
    def _call_seed(self, command_name):
        call_command(command_name, verbosity=0, stdout=StringIO())

    @override_settings(SEED_INITIAL_TEACHER_PASSWORD="123456")
    def test_teacher_seed_creates_complete_person_records_and_graduation_histories(self):
        PersonType.objects.create(code="instructor", display_name="Professor")

        self._call_seed("seed_system_initial_belt_ranks")
        self._call_seed("seed_system_initial_teacher")
        self._call_seed("seed_system_initial_teacher")

        expected_current = {
            "755.980.941-34": ("adult-black", 2),
            "920.000.004-52": ("adult-black", 1),
            "920.000.001-00": ("adult-black", 1),
            "920.000.005-33": ("adult-brown", 4),
            "920.000.002-90": ("adult-black", 0),
        }
        for cpf, (belt_code, grade_number) in expected_current.items():
            person = Person.objects.get(cpf=cpf)
            current = get_current_graduation(person)
            self.assertEqual(current.belt_rank.code, belt_code)
            self.assertEqual(current.grade_number, grade_number)
            self.assertEqual(person.martial_art, "jiu_jitsu")
            self.assertEqual(person.martial_art_started_at, person.graduations.order_by("awarded_at").first().awarded_at)
            self.assertEqual(person.martial_art_last_graduation_at, current.awarded_at)
            self.assertTrue(person.blood_type)
            self.assertTrue(person.allergies)
            self.assertTrue(person.previous_injuries)
            self.assertTrue(person.emergency_contact)
            self.assertTrue(person.previous_academy)
            self.assertEqual(
                person.graduations.values("belt_rank_id", "grade_number", "awarded_at")
                .distinct()
                .count(),
                person.graduations.count(),
            )

        self.assertEqual(
            Person.objects.get(cpf="920.000.005-33").graduations.count(),
            20,
        )
        self.assertEqual(
            Person.objects.get(cpf="755.980.941-34").graduations.count(),
            23,
        )

    @override_settings(
        SEED_INITIAL_ADMINISTRATIVE_PASSWORD="123456",
    )
    def test_administrative_seed_creates_complete_person_record_with_graduation_history(self):
        PersonType.objects.create(
            code="administrative-assistant",
            display_name="Administrativo",
        )

        self._call_seed("seed_system_initial_belt_ranks")
        self._call_seed("seed_system_initial_administrative")
        self._call_seed("seed_system_initial_administrative")

        person = Person.objects.get(cpf="920.000.001-01")
        current = get_current_graduation(person)
        self.assertEqual(current.belt_rank.code, "adult-purple")
        self.assertEqual(current.grade_number, 1)
        self.assertEqual(person.martial_art, "jiu_jitsu")
        self.assertEqual(person.martial_art_started_at, date(2019, 6, 11))
        self.assertEqual(person.martial_art_last_graduation_at, current.awarded_at)
        self.assertEqual(person.blood_type, "O+")
        self.assertTrue(person.allergies)
        self.assertTrue(person.previous_injuries)
        self.assertTrue(person.emergency_contact)
        self.assertEqual(person.graduations.count(), 12)

