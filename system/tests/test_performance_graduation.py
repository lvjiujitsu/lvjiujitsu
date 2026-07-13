from datetime import date, time, timedelta

from django.test import TestCase
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
    GraduationRule,
    IbjjfAgeCategory,
    Person,
    PersonType,
    TrainingStyle,
    WeekdayCode,
)
from system.models.calendar import CheckinStatus, ClassCheckin
from system.services.graduation import compute_graduation_progress, register_graduation
from system.selectors.graduation import get_graduation_overview

STUDENT_COUNT = 25


class GraduationOverviewQueryBudgetTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student_type = PersonType.objects.create(code="student", display_name="Aluno")
        cls.instructor_type = PersonType.objects.create(code="instructor", display_name="Professor")
        cls.category = ClassCategory.objects.create(
            code="adult", display_name="Adulto", audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-age-perf", display_name="Adulto",
            audience=CategoryAudience.ADULT, minimum_age=18, maximum_age=99,
        )
        cls.white = BeltRank.objects.create(
            code="adult-white-perf", display_name="Branca Perf",
            audience=CategoryAudience.ADULT, color_hex="#fff",
            max_grades=4, display_order=10,
        )
        cls.blue = BeltRank.objects.create(
            code="adult-blue-perf", display_name="Azul Perf",
            audience=CategoryAudience.ADULT, color_hex="#2563eb",
            max_grades=4, display_order=20,
        )
        cls.white.next_rank = cls.blue
        cls.white.save()
        GraduationRule.objects.create(
            belt_rank=cls.white, from_grade=0, to_grade=1,
            min_months_in_current_grade=4, min_classes_required=2,
            min_classes_window_months=12, is_active=True,
        )
        cls.instructor = Person.objects.create(
            full_name="Prof. Perf", cpf="801.000.000-00",
            person_type=cls.instructor_type, birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        cls.group = ClassGroup.objects.create(
            display_name="Turma Perf",
            class_category=cls.category, main_teacher=cls.instructor,
        )
        today = timezone.localdate()
        weekday_map = {
            0: WeekdayCode.MONDAY, 1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY, 3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY, 5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        cls.schedule = ClassSchedule.objects.create(
            class_group=cls.group,
            weekday=weekday_map[today.weekday()],
            start_time=time(19, 0),
            training_style=TrainingStyle.GI,
        )

        cls.students = []
        for i in range(STUDENT_COUNT):
            person = Person.objects.create(
                full_name=f"Aluno Perf {i:02d}",
                cpf=f"801.000.{i:03d}-{(i % 90) + 1:02d}",
                person_type=cls.student_type,
                birth_date=date(2000, 1, 1),
                biological_sex=BiologicalSex.MALE,
            )
            ClassEnrollment.objects.create(class_group=cls.group, person=person, status="active")
            cls.students.append(person)

        for i, person in enumerate(cls.students):
            if i % 3 == 0:
                register_graduation(
                    person=person, belt_rank=cls.white, grade_number=0,
                    awarded_at=timezone.localdate() - timedelta(days=200),
                )
                cls._create_approved_checkin(person, days_back=10)
                cls._create_approved_checkin(person, days_back=20)
            elif i % 3 == 1:
                register_graduation(
                    person=person, belt_rank=cls.white, grade_number=0,
                    awarded_at=timezone.localdate() - timedelta(days=30),
                )

    @classmethod
    def _create_approved_checkin(cls, person, days_back):
        target_date = timezone.localdate() - timedelta(days=days_back)
        session, _ = ClassSession.objects.get_or_create(schedule=cls.schedule, date=target_date)
        return ClassCheckin.objects.create(session=session, person=person, status=CheckinStatus.APPROVED)

    def test_query_count_does_not_grow_linearly_with_student_count(self):
        with self.assertNumQueries(5):
            rows = get_graduation_overview()
        self.assertEqual(len(rows), STUDENT_COUNT)

    def test_bulk_overview_matches_single_person_computation(self):
        reference_date = timezone.localdate()
        rows_by_person_id = {row.person.pk: row for row in get_graduation_overview(reference_date=reference_date)}

        self.assertEqual(len(rows_by_person_id), STUDENT_COUNT)

        for person in self.students:
            bulk_row = rows_by_person_id[person.pk]
            single_row = compute_graduation_progress(person, reference_date=reference_date)

            self.assertEqual(bulk_row.current_belt_rank, single_row.current_belt_rank)
            self.assertEqual(bulk_row.current_grade_number, single_row.current_grade_number)
            self.assertEqual(bulk_row.target_belt_rank, single_row.target_belt_rank)
            self.assertEqual(bulk_row.target_grade_number, single_row.target_grade_number)
            self.assertEqual(bulk_row.approved_classes_in_window, single_row.approved_classes_in_window)
            self.assertEqual(bulk_row.missing_classes, single_row.missing_classes)
            self.assertEqual(bulk_row.months_remaining, single_row.months_remaining)
            self.assertEqual(bulk_row.is_eligible, single_row.is_eligible)
            self.assertEqual(bulk_row.progress_pct, single_row.progress_pct)
            self.assertEqual(bulk_row.blocker, single_row.blocker)
