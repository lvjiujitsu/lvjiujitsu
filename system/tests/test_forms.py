from django.test import TestCase

from system.forms import ClassGroupForm
from system.services.seeding import seed_class_categories, seed_person_types


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
