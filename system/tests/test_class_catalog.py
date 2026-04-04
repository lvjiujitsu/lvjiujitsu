from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from system.models import (
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    PersonType,
)
from system.services.seeding import (
    seed_class_catalog,
    seed_class_categories,
    seed_class_matrix,
    seed_ibjjf_age_categories,
    seed_person_types,
)


class ClassCatalogModelTestCase(TestCase):
    def setUp(self):
        seed_person_types()
        seed_class_categories()
        seed_ibjjf_age_categories()

    def test_class_instructor_assignment_requires_administrative_or_instructor_type(self):
        class_group = ClassGroup.objects.create(
            code="test-class",
            display_name="Jiu Jitsu",
        )
        student_type = PersonType.objects.get(code="student")
        student = Person.objects.create(
            full_name="Aluno Sem Permissao",
            cpf="100.000.000-01",
        )
        student.person_types.add(student_type)

        assignment = ClassInstructorAssignment(
            class_group=class_group,
            person=student,
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_class_enrollment_requires_student_or_dependent_type(self):
        class_group = ClassGroup.objects.create(
            code="test-class-2",
            display_name="Jiu Jitsu",
        )
        guardian_type = PersonType.objects.get(code="guardian")
        guardian = Person.objects.create(
            full_name="Responsavel Sem Matricula",
            cpf="100.000.000-02",
        )
        guardian.person_types.add(guardian_type)

        enrollment = ClassEnrollment(
            class_group=class_group,
            person=guardian,
        )

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_class_group_requires_category_with_matching_audience(self):
        adult_category = ClassCategory.objects.get(code="adult")
        class_group = ClassGroup(
            code="kids-mismatch",
            display_name="Jiu Jitsu",
            audience="kids",
            class_category=adult_category,
        )

        with self.assertRaises(ValidationError):
            class_group.full_clean()

    def test_class_group_requires_instructor_as_main_teacher(self):
        adult_category = ClassCategory.objects.get(code="adult")
        guardian_type = PersonType.objects.get(code="guardian")
        guardian = Person.objects.create(
            full_name="Responsável Sem Permissão",
            cpf="100.000.000-03",
        )
        guardian.person_types.add(guardian_type)

        class_group = ClassGroup(
            code="adult-invalid-teacher",
            display_name="Jiu Jitsu",
            audience="adult",
            class_category=adult_category,
            main_teacher=guardian,
        )

        with self.assertRaises(ValidationError):
            class_group.full_clean()

    def test_seed_class_catalog_creates_official_groups_and_schedules(self):
        result = seed_class_catalog()

        self.assertEqual(ClassGroup.objects.count(), 6)
        self.assertEqual(ClassSchedule.objects.count(), 19)
        self.assertEqual(len(result["teachers"]), 5)

        adult_layon_group = ClassGroup.objects.get(code="adult-layon")
        self.assertEqual(adult_layon_group.display_name, "Jiu Jitsu")
        self.assertEqual(adult_layon_group.main_teacher.full_name, "Layon Quirino")
        self.assertEqual(adult_layon_group.class_category.code, "adult")
        self.assertEqual(adult_layon_group.schedules.count(), 5)
        self.assertTrue(
            adult_layon_group.schedules.filter(
                weekday="wednesday",
                training_style="no_gi",
            ).exists()
        )

    def test_seed_class_matrix_creates_cross_product_for_admin_assistants_and_students(self):
        result = seed_class_matrix()

        class_count = len(result["catalog"]["class_groups"])
        matrix_people = result["matrix_people"]
        assistant_people = [
            person
            for person in matrix_people
            if person.has_type_code("administrative-assistant")
        ]
        student_people = [
            person
            for person in matrix_people
            if person.has_type_code("student", "dependent")
        ]

        self.assertEqual(class_count, 6)
        self.assertEqual(
            len(result["instructor_assignments"]),
            len(assistant_people) * class_count,
        )
        self.assertEqual(len(result["enrollments"]), len(student_people) * class_count)

        for person in assistant_people:
            self.assertEqual(person.class_instructor_assignments.count(), class_count)

        for person in student_people:
            self.assertEqual(person.class_enrollments.count(), class_count)

    def test_person_computes_ibjjf_category_from_birth_date(self):
        seed_ibjjf_age_categories()
        person = Person.objects.create(
            full_name="Atleta Juvenil",
            cpf="111.222.333-44",
            birth_date=date(2010, 4, 4),
        )

        category = person.current_ibjjf_category

        self.assertIsNotNone(category)
        self.assertEqual(category.code, "juvenile-1")
