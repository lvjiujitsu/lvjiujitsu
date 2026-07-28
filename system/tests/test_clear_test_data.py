
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from system.models import BeltRank, ClassCategory, Person, PersonType
from system.tests.seed_helpers import DEFAULT_SEED_PASSWORD

TEST_PASSWORD = "LvTest@2026"


@override_settings(SEED_TEST_PORTAL_PASSWORD=TEST_PASSWORD)
class ClearTestDataTests(TestCase):
    def setUp(self):
        with self.settings(SEED_INITIAL_TEACHER_PASSWORD=DEFAULT_SEED_PASSWORD):
            for command_name in (
                "seed_system_initial_person_type",
                "seed_system_initial_belt_ranks",
                "seed_system_initial_ibjjf_age_categories",
                "seed_system_initial_class_categories",
                "seed_system_initial_teacher",
                "seed_system_initial_class_catalog",
            ):
                call_command(command_name, stdout=StringIO())

        self.reference_counts = {
            "person_types": PersonType.objects.count(),
            "belt_ranks": BeltRank.objects.count(),
            "class_categories": ClassCategory.objects.count(),
        }
        self.people_before_fixtures = Person.objects.count()

        for command_name in (
            "seed_system_initial_test_students",
            "seed_system_initial_test_guardians",
            "seed_system_initial_test_administrative",
            "seed_system_initial_test_teachers",
        ):
            call_command(command_name, stdout=StringIO())

    def test_requires_confirmation(self):
        with self.assertRaises(CommandError) as raised:
            call_command("clear_test_data", "--confirm", "ERRADO", stdout=StringIO())

        self.assertIn("CLEAR_TEST_DATA", str(raised.exception))

    def test_confirmation_is_mandatory(self):
        with self.assertRaises(CommandError):
            call_command("clear_test_data", stdout=StringIO())

    @override_settings(DJANGO_ENVIRONMENT="prod")
    def test_production_requires_explicit_flag(self):
        with self.assertRaises(CommandError) as raised:
            call_command(
                "clear_test_data", "--confirm", "CLEAR_TEST_DATA", stdout=StringIO()
            )

        self.assertIn("allow-production", str(raised.exception))

    def test_removes_fixture_people_and_preserves_reference_data(self):
        self.assertGreater(
            Person.objects.count(),
            self.people_before_fixtures,
            "As seeds ficticias precisam ter criado pessoas para o teste valer.",
        )

        call_command(
            "clear_test_data", "--confirm", "CLEAR_TEST_DATA", stdout=StringIO()
        )

        self.assertEqual(Person.objects.count(), self.people_before_fixtures)
        self.assertEqual(
            {
                "person_types": PersonType.objects.count(),
                "belt_ranks": BeltRank.objects.count(),
                "class_categories": ClassCategory.objects.count(),
            },
            self.reference_counts,
            "As seeds iniciais de referencia nao podem ser tocadas.",
        )

    def test_is_idempotent(self):
        call_command(
            "clear_test_data", "--confirm", "CLEAR_TEST_DATA", stdout=StringIO()
        )
        call_command(
            "clear_test_data", "--confirm", "CLEAR_TEST_DATA", stdout=StringIO()
        )

        self.assertEqual(Person.objects.count(), self.people_before_fixtures)
