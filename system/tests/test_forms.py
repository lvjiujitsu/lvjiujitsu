from datetime import date

from django.test import TestCase

from system.forms import ClassGroupForm, PersonForm
from system.models import BiologicalSex, ClassCategory, ClassEnrollment, Person, PersonType
from system.services.class_overview import build_class_group_filter_value
from system.services.registration import sync_person_class_enrollments
from system.services.seeding import seed_class_catalog, seed_class_categories, seed_person_types


class ClassGroupFormTestCase(TestCase):
    def setUp(self):
        seed_person_types()
        seed_class_categories()

    def test_active_class_group_requires_main_teacher(self):
        adult_category = (
            __import__("system.models", fromlist=["ClassCategory"])
            .ClassCategory.objects.get(code="adult")
        )

        form = ClassGroupForm(
            data={
                "code": "adult-without-teacher",
                "display_name": "Jiu Jitsu",
                "class_category": adult_category.pk,
                "description": "Turma ativa sem professor principal.",
                "default_capacity": 20,
                "is_active": "on",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("main_teacher", form.errors)


class PersonFormTestCase(TestCase):
    def setUp(self):
        seed_class_catalog()
        self.person_types = seed_person_types()
        self.adult_category = ClassCategory.objects.get(code="adult")
        self.student_type = PersonType.objects.get(code="student")
        self.logical_adult_key = build_class_group_filter_value(
            self.adult_category.pk,
            "Jiu Jitsu",
        )

    def test_person_form_exposes_logical_class_choices_and_expands_enrollments(self):
        form = PersonForm(
            data={
                "full_name": "Aluno Logico",
                "cpf": "55544433322",
                "birth_date": "1994-08-12",
                "biological_sex": BiologicalSex.MALE,
                "person_type": self.student_type.pk,
                "class_groups": [self.logical_adult_key],
                "is_active": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        person = form.save()

        choices = [label for value, label in form.fields["class_groups"].choices]
        self.assertEqual(choices.count("Adulto · Jiu Jitsu"), 1)
        self.assertEqual(
            set(
                ClassEnrollment.objects.filter(person=person).values_list(
                    "class_group__code",
                    flat=True,
                )
            ),
            {"adult-lauro", "adult-layon", "adult-vinicius"},
        )

    def test_person_form_initial_selection_collapses_logical_group_once(self):
        person = Person.objects.create(
            full_name="Aluno Existente",
            cpf="55544433321",
            birth_date=date(1994, 8, 12),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
            class_category=self.adult_category,
        )
        sync_person_class_enrollments(
            person,
            list(self.adult_category.class_groups.filter(display_name="Jiu Jitsu")),
        )

        form = PersonForm(instance=person)

        self.assertEqual(form["class_groups"].value(), [self.logical_adult_key])
