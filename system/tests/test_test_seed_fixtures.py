import json
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from system.models import (
    ClassEnrollment,
    ClassInstructorAssignment,
    Graduation,
    Person,
    PersonOperationalRole,
    PersonRelationship,
)
from system.services.test_seed_fixtures import REQUIRED_ENTRY_KEYS, TEST_SEED_NOTE
from system.tests.seed_helpers import DEFAULT_SEED_PASSWORD


TEST_FIXTURE_FILES = (
    "seed_system_initial_test_students.json",
    "seed_system_initial_test_guardians.json",
    "seed_system_initial_test_administrative.json",
    "seed_system_initial_test_teachers.json",
)


class TestSeedFixtureJsonContractTestCase(SimpleTestCase):
    def test_test_seed_json_files_parse_and_cover_expected_matrix(self):
        entries = _load_test_fixture_entries()

        for entry in entries:
            self.assertEqual(sorted(REQUIRED_ENTRY_KEYS - set(entry)), [])

        self.assertEqual(
            {entry["blood_type"] for entry in entries},
            {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"},
        )
        expected_martial_arts = {
            "",
            "jiu_jitsu",
            "muay_thai",
            "judo",
            "karate",
            "boxing",
            "wrestling",
            "other",
        }
        self.assertTrue(
            expected_martial_arts.issubset({entry["martial_art"] for entry in entries})
        )

        belt_codes = {
            history["belt_rank_code"]
            for entry in entries
            for history in entry["graduation_history"]
        }
        self.assertTrue(
            {
                "kids-white",
                "kids-grey",
                "kids-yellow",
                "kids-orange",
                "kids-green",
                "adult-white",
                "adult-blue",
                "adult-purple",
                "adult-brown",
                "adult-black",
                "adult-coral-redblack",
                "adult-coral-redwhite",
                "adult-red",
            }.issubset(belt_codes)
        )

        tags = {tag for entry in entries for tag in entry["coverage_tags"]}
        self.assertTrue(
            {
                "dependency:holder-with-dependent",
                "dependency:multiple-dependents",
                "dependency:dual-guardian-target",
                "dependency:administrative-with-dependent",
                "dependency:teacher-with-dependent",
                "visual:admin-upgrade-toggle",
                "visual:delete-candidate",
                "role:all",
            }.issubset(tags)
        )


class TestSeedFixtureCommandTestCase(TestCase):
    def test_test_seed_commands_are_idempotent_and_create_core_links(self):
        self._seed_dependencies()

        commands = (
            "seed_system_initial_test_students",
            "seed_system_initial_test_guardians",
            "seed_system_initial_test_administrative",
            "seed_system_initial_test_teachers",
        )
        for command_name in commands:
            self._call(command_name)
            self._call(command_name)

        test_cpfs = _load_test_fixture_cpfs()
        self.assertEqual(Person.objects.filter(cpf__in=test_cpfs).count(), 31)
        self.assertEqual(
            ClassEnrollment.objects.filter(person__cpf__in=test_cpfs).count(),
            17,
        )
        self.assertEqual(PersonRelationship.objects.filter(notes=TEST_SEED_NOTE).count(), 11)
        self.assertEqual(PersonOperationalRole.objects.filter(notes=TEST_SEED_NOTE).count(), 17)
        self.assertEqual(ClassInstructorAssignment.objects.filter(notes=TEST_SEED_NOTE).count(), 9)

        student = Person.objects.get(cpf="930.100.004-04")
        self.assertTrue(student.access_account.check_password("LvTest@2026"))
        self.assertFalse(student.operational_role_assignments.exists())

        student_assistant = Person.objects.get(cpf="930.100.006-06")
        self.assertTrue(student_assistant.has_operational_role("class-assistant"))
        self.assertEqual(student_assistant.class_instructor_assignments.count(), 1)

        all_roles_admin = Person.objects.get(cpf="930.300.003-03")
        self.assertEqual(all_roles_admin.operational_role_assignments.count(), 6)

        dual_guardian_dependent = Person.objects.get(cpf="930.100.008-08")
        self.assertEqual(dual_guardian_dependent.incoming_relationships.count(), 2)

        teacher_with_dependent = Person.objects.get(cpf="930.400.002-02")
        self.assertEqual(teacher_with_dependent.outgoing_relationships.count(), 1)

        self.assertTrue(
            Graduation.objects.filter(
                person__cpf="930.400.003-03",
                belt_rank__code="adult-coral-redblack",
            ).exists()
        )
        self.assertTrue(
            Graduation.objects.filter(
                person__cpf="930.100.008-08",
                belt_rank__code="kids-grey",
            ).exists()
        )

    def _seed_dependencies(self):
        with self.settings(SEED_INITIAL_TEACHER_PASSWORD=DEFAULT_SEED_PASSWORD):
            self._call("seed_system_initial_person_type")
            self._call("seed_system_initial_belt_ranks")
            self._call("seed_system_initial_ibjjf_age_categories")
            self._call("seed_system_initial_class_categories")
            self._call("seed_system_initial_teacher")
            self._call("seed_system_initial_class_catalog")

    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())


def _load_test_fixture_entries():
    entries = []
    for filename in TEST_FIXTURE_FILES:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / filename
        with path.open(encoding="utf-8") as file:
            entries.extend(json.load(file))
    return entries


def _load_test_fixture_cpfs():
    return {entry["cpf"] for entry in _load_test_fixture_entries()}
