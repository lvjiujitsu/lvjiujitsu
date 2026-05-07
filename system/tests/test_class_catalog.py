from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from system.models import (
    BiologicalSex,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    PersonType,
    TeacherPayrollConfig,
)
from system.services.payroll_rules import decode_payroll_rules
from system.services.seeding import (
    seed_belts,
    seed_class_catalog,
    seed_class_categories,
    seed_graduation_rules,
    seed_ibjjf_age_categories,
    seed_official_instructors,
    seed_person_administrative,
    seed_person_types,
    seed_teacher_payroll_configs,
)


class ClassCatalogModelTestCase(TestCase):
    def setUp(self):
        seed_person_types()
        seed_class_categories()
        seed_ibjjf_age_categories()
        seed_belts()
        seed_graduation_rules()
        seed_official_instructors()

    def test_class_instructor_assignment_requires_administrative_or_instructor_type(self):
        adult_category = ClassCategory.objects.get(code="adult")
        class_group = ClassGroup.objects.create(
            code="test-class",
            display_name="Jiu Jitsu",
            class_category=adult_category,
        )
        student_type = PersonType.objects.get(code="student")
        student = Person.objects.create(
            full_name="Aluno Sem Permissao",
            cpf="100.000.000-01",
            person_type=student_type,
        )

        assignment = ClassInstructorAssignment(
            class_group=class_group,
            person=student,
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_class_enrollment_requires_student_or_dependent_type(self):
        adult_category = ClassCategory.objects.get(code="adult")
        class_group = ClassGroup.objects.create(
            code="test-class-2",
            display_name="Jiu Jitsu",
            class_category=adult_category,
        )
        guardian_type = PersonType.objects.get(code="guardian")
        guardian = Person.objects.create(
            full_name="Responsável Sem Matrícula",
            cpf="100.000.000-02",
            person_type=guardian_type,
        )

        enrollment = ClassEnrollment(
            class_group=class_group,
            person=guardian,
        )

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_class_enrollment_blocks_male_student_from_women_group(self):
        women_category = ClassCategory.objects.get(code="women")
        class_group = ClassGroup.objects.create(
            code="women-class",
            display_name="Jiu Jitsu",
            class_category=women_category,
        )
        student_type = PersonType.objects.get(code="student")
        student = Person.objects.create(
            full_name="Aluno Masculino",
            cpf="100.000.000-04",
            birth_date=date(1995, 4, 4),
            biological_sex=BiologicalSex.MALE,
            person_type=student_type,
        )

        enrollment = ClassEnrollment(class_group=class_group, person=student)

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_class_enrollment_blocks_adult_student_from_kids_group(self):
        kids_category = ClassCategory.objects.get(code="kids")
        class_group = ClassGroup.objects.create(
            code="kids-class",
            display_name="Jiu Jitsu",
            class_category=kids_category,
        )
        student_type = PersonType.objects.get(code="student")
        student = Person.objects.create(
            full_name="Aluno Adulto",
            cpf="100.000.000-05",
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            person_type=student_type,
        )

        enrollment = ClassEnrollment(class_group=class_group, person=student)

        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_class_group_requires_instructor_as_main_teacher(self):
        adult_category = ClassCategory.objects.get(code="adult")
        guardian_type = PersonType.objects.get(code="guardian")
        guardian = Person.objects.create(
            full_name="Responsável Sem Permissão",
            cpf="100.000.000-03",
            person_type=guardian_type,
        )

        class_group = ClassGroup(
            code="adult-invalid-teacher",
            display_name="Jiu Jitsu",
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
        self.assertEqual(adult_layon_group.main_teacher.person_type.code, "instructor")
        self.assertEqual(adult_layon_group.class_category.code, "adult")
        self.assertEqual(adult_layon_group.schedules.count(), 5)
        self.assertTrue(
            adult_layon_group.schedules.filter(
                weekday="wednesday",
                training_style="no_gi",
            ).exists()
        )

    def test_seed_teacher_payroll_configs_creates_default_payroll_rules(self):
        seed_class_catalog()
        seed_teacher_payroll_configs()

        layon = Person.objects.get(full_name="Layon Quirino")
        vinicius = Person.objects.get(full_name="Vinicius Antonio")
        andre = Person.objects.get(full_name="Andre Oliveira")
        vanessa = Person.objects.get(full_name="Vanessa Ferro")

        layon_rules = decode_payroll_rules(layon.payroll_config.notes)["rules"]
        self.assertEqual(layon.payroll_config.monthly_salary, 400)
        self.assertTrue(
            any(
                rule["method"] == "student_percentage"
                and rule["percentage"] == "50.00"
                and rule["class_group_code"] == "juvenile-layon"
                for rule in layon_rules
            )
        )
        self.assertEqual(vinicius.payroll_config.monthly_salary, 400)
        self.assertEqual(andre.payroll_config.monthly_salary, 0)
        self.assertEqual(vanessa.payroll_config.monthly_salary, 0)
        self.assertEqual(TeacherPayrollConfig.objects.count(), 5)

    def test_seed_person_administrative_creates_single_type_account(self):
        result = seed_person_administrative()

        self.assertEqual(result["administrative"].person_type.code, "administrative-assistant")
        self.assertTrue(result["administrative"].has_portal_access)

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
