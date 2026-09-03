from io import StringIO
import os
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from system.management.commands.clear_migration_supabase_hg import Command as HgCommand
from system.management.commands.clear_migration_supabase_prod import Command as ProdCommand

MODULE = 'system.management.commands._supabase_public_schema_reset'


@override_settings(DJANGO_ENVIRONMENT='hg', DEBUG=False,
                   DATABASE_URL='postgresql://postgres:fixture@db.fixtureproject.supabase.co/postgres',
                   SUPABASE_PROJECT_REF='fixtureproject')
class RemoteResetParityTests(SimpleTestCase):
    def test_hg_defaults_to_simulation_without_destructive_sql(self):
        with mock.patch.dict(os.environ, {'SUPABASE_RESET_CONFIRM': 'RESET_HG'}), \
             mock.patch(f'{MODULE}.connection') as connection, \
             mock.patch.object(HgCommand, 'list_public_relations', return_value=[('r', 'fixture')]):
            connection.vendor = 'postgresql'
            call_command('clear_migration_supabase_hg', stdout=StringIO())
        connection.cursor.assert_not_called()

    def test_hg_refuses_missing_confirmation_before_querying(self):
        with mock.patch.dict(os.environ, {'SUPABASE_RESET_CONFIRM': ''}), \
             mock.patch(f'{MODULE}.connection') as connection:
            connection.vendor = 'postgresql'
            with self.assertRaisesMessage(CommandError, 'SUPABASE_RESET_CONFIRM=RESET_HG'):
                call_command('clear_migration_supabase_hg', '--execute', stdout=StringIO())
        connection.cursor.assert_not_called()

    def test_production_execute_requires_independent_ref_confirmation(self):
        with override_settings(DJANGO_ENVIRONMENT='prod'), \
             mock.patch.dict(os.environ, {'SUPABASE_RESET_CONFIRM': 'RESET_PROD'}), \
             mock.patch(f'{MODULE}.connection') as connection:
            connection.vendor = 'postgresql'
            with self.assertRaisesMessage(CommandError, '--confirm-ref'):
                call_command('clear_migration_supabase_prod', '--execute', stdout=StringIO())
        connection.cursor.assert_not_called()

    def test_similar_pooler_domain_is_refused(self):
        self.assertFalse(HgCommand.is_supabase_database_url('postgresql://u:p@evilpooler.supabase.com/db'))
        self.assertTrue(HgCommand.is_supabase_database_url('postgresql://u:p@aws-0-sa-east-1.pooler.supabase.com/db'))
