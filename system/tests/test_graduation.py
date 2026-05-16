from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
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
            code="grad-group", display_name="Turma",
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


class GraduationDashboardCardTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        self.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        self.white = BeltRank.objects.create(
            code="dashboard-white",
            display_name="Faixa Branca",
            audience=CategoryAudience.ADULT,
            color_hex="#ffffff",
            tip_color_hex="#000000",
            stripe_color_hex="#ffffff",
            max_grades=4,
            display_order=10,
        )
        GraduationRule.objects.create(
            belt_rank=self.white,
            from_grade=1,
            to_grade=2,
            min_months_in_current_grade=4,
            min_classes_required=8,
            min_classes_window_months=12,
            is_active=True,
        )

    def _create_account(self, *, person_type, cpf, full_name):
        person = Person.objects.create(
            full_name=full_name,
            cpf=cpf,
            person_type=person_type,
            birth_date=date(2000, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        Graduation.objects.create(
            person=person,
            belt_rank=self.white,
            grade_number=1,
            awarded_at=timezone.localdate() - timedelta(days=35),
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        return account

    def _login(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def assert_graduation_card_is_collapsed(self, response):
        html = response.content.decode()
        self.assertContains(response, "Minha faixa")
        self.assertContains(response, "Faixa Branca")
        self.assertContains(response, "Mais sobre a graduação")
        self.assertContains(response, "Tempo na faixa atual")
        self.assertContains(response, "Aulas aprovadas")
        self.assertIn('<details class="graduation-progress-details">', html)
        self.assertNotIn('<details class="graduation-progress-details" open', html)
        self.assertContains(response, "data-bjj-history-open")
        self.assertContains(response, "system/js/graduation/progress-card.js?v=20260507a")

    def test_student_home_collapses_graduation_details_by_default(self):
        account = self._create_account(
            person_type=self.student_type,
            cpf="800.222.222-01",
            full_name="Aluno Home Graduação",
        )
        self._login(account)

        response = self.client.get(reverse("system:student-home"))

        self.assertEqual(response.status_code, 200)
        self.assert_graduation_card_is_collapsed(response)

    def test_instructor_home_collapses_graduation_details_by_default(self):
        account = self._create_account(
            person_type=self.instructor_type,
            cpf="800.222.222-02",
            full_name="Professor Home Graduação",
        )
        self._login(account)

        response = self.client.get(reverse("system:instructor-home"))

        self.assertEqual(response.status_code, 200)
        self.assert_graduation_card_is_collapsed(response)


class GraduationViewTestCase(TestCase):
    def setUp(self):
        self.django_admin = User.objects.create_superuser(
            username="grad-admin", email="grad@admin.com", password="admin",
        )
        self.admin_type = PersonType.objects.create(
            code="administrative-assistant", display_name="Administrativo",
        )
        self.admin_person = Person.objects.create(
            full_name="Admin Grad", cpf="800.111.111-11", person_type=self.admin_type,
        )
        self.admin_account = PortalAccount(person=self.admin_person)
        self.admin_account.set_password("123456")
        self.admin_account.save()

    def _login_as_admin(self):
        self.client.force_login(self.django_admin)
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.admin_account.pk
        session[TECHNICAL_ADMIN_SESSION_KEY] = True
        session.save()

    def test_belt_rank_list_view(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:belt-rank-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Faixas")

    def test_belt_rank_create_view(self):
        self._login_as_admin()
        response = self.client.post(
            reverse("system:belt-rank-create"),
            data={
                "code": "test-belt",
                "display_name": "Faixa Teste",
                "audience": CategoryAudience.ADULT,
                "color_hex": "#abcdef",
                "tip_color_hex": "#000000",
                "stripe_color_hex": "#ffffff",
                "max_grades": 4,
                "min_age": 16,
                "max_age": "",
                "next_rank": "",
                "display_order": 50,
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BeltRank.objects.filter(code="test-belt").exists())

    def test_graduation_overview_view(self):
        self._login_as_admin()
        response = self.client.get(reverse("system:graduation-overview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panorama de graduação")
