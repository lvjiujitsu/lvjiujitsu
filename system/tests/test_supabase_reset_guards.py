
from __future__ import annotations

import os
from unittest import mock

from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from system.management.commands._supabase_public_schema_reset import (
    SupabasePublicSchemaResetCommand,
)

HG_URL = "postgresql://postgres.abcdefghijklmnop:senha@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
DIRECT_URL = "postgresql://postgres:senha@db.abcdefghijklmnop.supabase.co:5432/postgres"
PROJECT_REF = "abcdefghijklmnop"


class ResetCommand(SupabasePublicSchemaResetCommand):
    target_environment = "hg"
    confirmation_value = "RESET_HG"


class ProjectRefGuardTests(SimpleTestCase):

    def test_pooler_url_matching_project_ref_is_accepted(self):
        with override_settings(SUPABASE_PROJECT_REF=PROJECT_REF):
            self.assertEqual(
                ResetCommand.validate_project_ref(HG_URL), PROJECT_REF
            )

    def test_direct_url_matching_project_ref_is_accepted(self):
        with override_settings(SUPABASE_PROJECT_REF=PROJECT_REF):
            self.assertEqual(
                ResetCommand.validate_project_ref(DIRECT_URL), PROJECT_REF
            )

    def test_missing_project_ref_is_refused(self):
        with override_settings(SUPABASE_PROJECT_REF=""):
            with self.assertRaises(CommandError) as raised:
                ResetCommand.validate_project_ref(HG_URL)

        self.assertIn("SUPABASE_PROJECT_REF", str(raised.exception))

    def test_project_ref_from_another_project_is_refused(self):
        with override_settings(SUPABASE_PROJECT_REF="outroprojetoxxxxx"):
            with self.assertRaises(CommandError) as raised:
                ResetCommand.validate_project_ref(HG_URL)

        self.assertIn("nao corresponde", str(raised.exception))


class SafetyGuardTests(SimpleTestCase):

    def _validate(self, **overrides):
        defaults = {
            "DJANGO_ENVIRONMENT": "hg",
            "DEBUG": False,
            "DATABASE_URL": HG_URL,
            "SUPABASE_PROJECT_REF": PROJECT_REF,
        }
        defaults.update(overrides)
        confirm = overrides.pop("_confirm", "RESET_HG")
        with override_settings(**defaults):
            with mock.patch.dict(os.environ, {"SUPABASE_RESET_CONFIRM": confirm}):
                with mock.patch(
                    "system.management.commands._supabase_public_schema_reset.connection"
                ) as fake_connection:
                    fake_connection.vendor = "postgresql"
                    return ResetCommand().validate_safety_guards()

    def test_complete_configuration_is_accepted(self):
        self.assertEqual(self._validate(), PROJECT_REF)

    def test_wrong_environment_is_refused(self):
        with self.assertRaises(CommandError) as raised:
            self._validate(DJANGO_ENVIRONMENT="prod")

        self.assertIn("DJANGO_ENVIRONMENT=hg", str(raised.exception))

    def test_debug_true_is_refused(self):
        with self.assertRaises(CommandError) as raised:
            self._validate(DEBUG=True)

        self.assertIn("DJANGO_DEBUG=False", str(raised.exception))

    def test_empty_database_url_is_refused(self):
        with self.assertRaises(CommandError) as raised:
            self._validate(DATABASE_URL="")

        self.assertIn("DATABASE_URL", str(raised.exception))

    def test_non_supabase_host_is_refused(self):
        with self.assertRaises(CommandError) as raised:
            self._validate(DATABASE_URL="postgresql://u:p@db.example.com:5432/postgres")

        self.assertIn("host Supabase", str(raised.exception))

    def test_wrong_confirmation_is_refused(self):
        with self.assertRaises(CommandError) as raised:
            self._validate(_confirm="RESET_PROD")

        self.assertIn("SUPABASE_RESET_CONFIRM=RESET_HG", str(raised.exception))


class DryRunTests(SimpleTestCase):

    def test_dry_run_does_not_execute_destructive_sql(self):
        command = ResetCommand()
        executed = []

        with mock.patch.object(
            ResetCommand, "validate_safety_guards", return_value=PROJECT_REF
        ), mock.patch.object(
            ResetCommand,
            "list_public_relations",
            return_value=[("r", "system_person"), ("S", "system_person_id_seq")],
        ), mock.patch(
            "system.management.commands._supabase_public_schema_reset.connection"
        ) as fake_connection:
            cursor = fake_connection.cursor.return_value.__enter__.return_value
            cursor.execute.side_effect = lambda sql, *args: executed.append(sql)
            command.handle(execute=False)

        self.assertEqual(
            executed,
            [],
            "Modo simulacao nao pode emitir nenhum comando SQL destrutivo.",
        )
