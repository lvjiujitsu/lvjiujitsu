import json
import os
import shutil
import tempfile
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from clear_migrations import remove_runtime_artifacts
from system.constants import OperationalRoleCode, PersonTypeCode
from system.models import (
    BeltRank,
    CategoryAudience,
    Graduation,
    Holiday,
    Person,
    PersonRelationship,
    PlanPrice,
    PlanTier,
    SubscriptionPlan,
    TeacherPayrollConfig,
)
from system.services.payroll_rules import decode_payroll_rules
from system.tests.seed_helpers import DEFAULT_SEED_PASSWORD


class ClearMigrationsCleanupTestCase(SimpleTestCase):
    def test_remove_runtime_artifacts_also_removes_playwright_and_screenshot_dirs(self):
        root = Path(
            tempfile.mkdtemp(
                prefix="cleanup-artifacts-",
                dir=Path.cwd(),
            )
        )
        try:
            removed_paths = []

            def capture_remove_path(path):
                removed_paths.append(path)
                return False

            with (
                patch("clear_migrations.force_remove", side_effect=capture_remove_path),
                redirect_stdout(StringIO()),
            ):
                remove_runtime_artifacts(root)

            self.assertIn(root / ".playwright-mcp", removed_paths)
            self.assertIn(root / "test_artifacts", removed_paths)
            self.assertIn(root / "test_screenshots", removed_paths)
            self.assertNotIn(root / ".venv", removed_paths)
        finally:
            shutil.rmtree(root, ignore_errors=True)


class SeedCommandGovernanceTestCase(SimpleTestCase):
    def test_bootstrap_command_is_not_available(self):
        get_commands.cache_clear()

        self.assertNotIn("bootstrap", get_commands())

    def test_inicial_seed_command_is_not_available(self):
        get_commands.cache_clear()

        self.assertNotIn("inicial_seed", get_commands())

    def test_inicial_seed_test_command_is_not_available(self):
        get_commands.cache_clear()

        self.assertNotIn("inicial_seed_test", get_commands())

    def test_single_consumer_seed_json_files_follow_command_names(self):
        data_root = Path(settings.BASE_DIR) / "static" / "initial_data"
        expected_files = (
            "seed_system_initial_belt_ranks.json",
            "seed_system_initial_class_categories.json",
            "seed_system_initial_class_catalog.json",
            "seed_system_initial_ibjjf_age_categories.json",
            "seed_system_initial_holidays.json",
            "seed_system_initial_graduation_rules.json",
            "seed_system_initial_product_categories.json",
            "seed_system_initial_product_catalog.json",
            "seed_system_initial_product_catalog_inventory.json",
            "seed_system_initial_teacher_payroll_configs.json",
            "seed_system_initial_subscription_plans.json",
            "seed_system_initial_subscription_plans_values.json",
        )

        missing_files = [
            filename
            for filename in expected_files
            if not (data_root / filename).exists()
        ]

        self.assertEqual(missing_files, [])


class SupabaseResetCommandSafetyTestCase(SimpleTestCase):
    def _call(self, command_name, environment, confirm_value="", debug=False):
        stdout = StringIO()
        environ = {}
        if confirm_value:
            environ["SUPABASE_RESET_CONFIRM"] = confirm_value

        with (
            self.settings(
                DATABASE_URL="postgres://postgres.example:secret@db.example.supabase.co:5432/postgres",
                DEBUG=debug,
                DJANGO_ENVIRONMENT=environment,
            ),
            patch.dict(os.environ, environ, clear=False),
        ):
            call_command(command_name, stdout=stdout)

        return stdout.getvalue()

    def test_hg_reset_refuses_wrong_environment(self):
        with self.assertRaisesMessage(CommandError, "DJANGO_ENVIRONMENT=hg"):
            self._call(
                "clear_migration_supabase_hg",
                environment="prod",
                confirm_value="RESET_HG",
            )

    def test_hg_reset_refuses_debug_enabled(self):
        with self.assertRaisesMessage(CommandError, "DJANGO_DEBUG=False"):
            self._call(
                "clear_migration_supabase_hg",
                environment="hg",
                confirm_value="RESET_HG",
                debug=True,
            )

    def test_hg_reset_refuses_missing_confirmation(self):
        with self.assertRaisesMessage(CommandError, "SUPABASE_RESET_CONFIRM=RESET_HG"):
            self._call("clear_migration_supabase_hg", environment="hg")

    def test_hg_reset_refuses_sqlite_connection(self):
        with self.assertRaisesMessage(CommandError, "PostgreSQL"):
            self._call(
                "clear_migration_supabase_hg",
                environment="hg",
                confirm_value="RESET_HG",
            )

    def test_prod_reset_refuses_wrong_environment(self):
        with self.assertRaisesMessage(CommandError, "DJANGO_ENVIRONMENT=prod"):
            self._call(
                "clear_migration_supabase_prod",
                environment="hg",
                confirm_value="RESET_PROD",
            )

    def test_prod_reset_refuses_debug_enabled(self):
        with self.assertRaisesMessage(CommandError, "DJANGO_DEBUG=False"):
            self._call(
                "clear_migration_supabase_prod",
                environment="prod",
                confirm_value="RESET_PROD",
                debug=True,
            )

    def test_prod_reset_refuses_missing_confirmation(self):
        with self.assertRaisesMessage(CommandError, "SUPABASE_RESET_CONFIRM=RESET_PROD"):
            self._call("clear_migration_supabase_prod", environment="prod")

    def test_prod_reset_refuses_sqlite_connection(self):
        with self.assertRaisesMessage(CommandError, "PostgreSQL"):
            self._call(
                "clear_migration_supabase_prod",
                environment="prod",
                confirm_value="RESET_PROD",
            )


class TeacherPayrollSeedCommandTestCase(TestCase):
    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())

    def _seed_dependencies(self):
        self._call("seed_system_initial_person_type")
        self._call("seed_system_initial_belt_ranks")
        self._call("seed_system_initial_teacher")
        self._call("seed_system_initial_class_categories")
        self._call("seed_system_initial_class_categories_teacher")
        self._call("seed_system_initial_class_catalog")

    def test_seed_system_initial_teacher_payroll_configs_creates_idempotent_configs(self):
        self._seed_dependencies()

        self._call("seed_system_initial_teacher_payroll_configs")
        self._call("seed_system_initial_teacher_payroll_configs")

        self.assertEqual(TeacherPayrollConfig.objects.count(), 5)

        layon = TeacherPayrollConfig.objects.select_related("person").get(
            person__cpf="920.000.001-00"
        )
        self.assertEqual(layon.monthly_salary, Decimal("400.00"))
        self.assertEqual(layon.payment_day, 28)

        rules = decode_payroll_rules(layon.notes, strict=True)["rules"]
        self.assertEqual(len(rules), 2)
        self.assertTrue(all("class_group_id" in rule for rule in rules))
        self.assertTrue(all("class_group_code" not in rule for rule in rules))

        zero_configs = TeacherPayrollConfig.objects.filter(monthly_salary=Decimal("0.00"))
        self.assertEqual(zero_configs.count(), 3)


class HolidaySeedCommandTestCase(TestCase):
    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())

    def test_seed_system_initial_holidays_creates_idempotent_holidays(self):
        self._call("seed_system_initial_holidays")
        self._call("seed_system_initial_holidays")

        self.assertEqual(Holiday.objects.count(), 13)

        new_year = Holiday.objects.get(date="2026-01-01")
        self.assertEqual(new_year.name, "Confraternização Universal")
        self.assertTrue(new_year.is_active)

        corpus_christi = Holiday.objects.get(date="2026-06-04")
        self.assertEqual(corpus_christi.name, "Corpus Christi")


class AdministrativeSeedCommandTestCase(TestCase):
    @staticmethod
    def _call(command_name):
        call_command(command_name, stdout=StringIO())

    def _seed_person_types_and_belts(self):
        self._call("seed_system_initial_person_type")
        self._call("seed_system_initial_belt_ranks")

    def _seed_full_administrative_dependencies(self):
        self._seed_person_types_and_belts()
        self._call("seed_system_initial_ibjjf_age_categories")
        self._call("seed_system_initial_class_categories")
        self._call("seed_system_initial_teacher")
        self._call("seed_system_initial_class_catalog")

    def _administrative_password_settings(self):
        return self.settings(
            SEED_INITIAL_ADMINISTRATIVE_PASSWORD=DEFAULT_SEED_PASSWORD,
            SEED_INITIAL_TEACHER_PASSWORD=DEFAULT_SEED_PASSWORD,
        )

    def test_administrative_seed_reports_missing_class_categories_before_partial_write(self):
        with self._administrative_password_settings():
            self._seed_person_types_and_belts()

            with self.assertRaisesMessage(CommandError, "seed_system_initial_class_categories"):
                self._call("seed_system_initial_administrative")

        self.assertFalse(Person.objects.filter(cpf="920.000.011-81").exists())

    def test_administrative_seed_reports_missing_class_catalog_before_partial_write(self):
        with self._administrative_password_settings():
            self._seed_person_types_and_belts()
            self._call("seed_system_initial_class_categories")
            self._call("seed_system_initial_teacher")

            with self.assertRaisesMessage(CommandError, "seed_system_initial_class_catalog"):
                self._call("seed_system_initial_administrative")

        self.assertFalse(Person.objects.filter(cpf="920.000.011-81").exists())

    def test_administrative_legacy_link_seeds_are_idempotent_after_main_seed(self):
        with self._administrative_password_settings():
            self._seed_full_administrative_dependencies()
            self._call("seed_system_initial_administrative")
            self._call("seed_system_initial_class_categories_administrative")
            self._call("seed_system_initial_class_categories_administrative")
            self._call("seed_system_initial_class_catalog_administrative")
            self._call("seed_system_initial_class_catalog_administrative")

        person = Person.objects.get(cpf="920.000.011-81")
        self.assertEqual(person.person_type.code, PersonTypeCode.STUDENT)
        self.assertEqual(person.class_category.code, "adult")
        self.assertEqual(person.class_enrollments.filter(status="active").count(), 2)
        self.assertTrue(person.has_operational_role(OperationalRoleCode.CLASS_ASSISTANT))
        self.assertEqual(
            person.operational_role_assignments.get().class_group.class_category.code,
            "kids",
        )
        self.assertEqual(person.class_instructor_assignments.count(), 1)
        self.assertEqual(
            person.class_instructor_assignments.get().class_group.class_category.code,
            "kids",
        )
        miguel = Person.objects.get(cpf="920.000.012-62")
        self.assertEqual(miguel.person_type.code, PersonTypeCode.STUDENT)
        self.assertFalse(miguel.operational_role_assignments.exists())


class KanriStudentsMigrationSeedCommandTestCase(TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="kanri-seed-", dir=Path.cwd()))
        self.data_dir = self.root / "static" / "initial_data" / "kanri_students_migration"
        self.data_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _call_seed(self):
        stdout = StringIO()
        with self.settings(BASE_DIR=self.root):
            call_command("seed_system_initial_kanri_students_migration", stdout=stdout)
        return stdout.getvalue()

    def _seed_person_types(self):
        call_command("seed_system_initial_person_type", stdout=StringIO())

    def _seed_belt_ranks(self):
        BeltRank.objects.create(
            code="kids-white",
            display_name="Branca (Infantil)",
            audience=CategoryAudience.KIDS,
            min_age=4,
            max_age=15,
            display_order=10,
        )
        BeltRank.objects.create(
            code="adult-white",
            display_name="Branca",
            audience=CategoryAudience.ADULT,
            min_age=16,
            display_order=100,
        )
        BeltRank.objects.create(
            code="adult-blue",
            display_name="Azul",
            audience=CategoryAudience.ADULT,
            min_age=16,
            display_order=110,
        )

    def _write_student(self, filename, payload):
        path = self.data_dir / filename
        path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

    def _base_payload(self, **overrides):
        payload = {
            "email": "aluno@example.com",
            "nome": "Aluno Teste",
            "sexo": "Masculino",
            "nascimento": "2016-01-22",
            "tipo_documento": "CPF Pai",
            "n_documento": "11122233344",
            "telefone": "62999990000",
            "endereco": {
                "cep": "74672-550",
                "logradouro": "Rua do Angico",
                "numero": "01",
                "complemento": "",
                "bairro": "Santa Genoveva",
                "cidade": "Goiânia",
                "uf": "GO",
            },
            "responsavel": {
                "nome": "Responsavel Teste",
                "email": "responsavel@example.com",
                "vinculo": "Pai",
                "telefone": "62 98888-7777",
                "tipo_documento": "CPF",
                "n_documento": "11122233344",
                "observacoes": "Responsável financeiro",
                "responsavel_financeiro": True,
            },
            "financeiro": [
                {
                    "tipo_lancamento": "Mensalidade",
                    "descricao": "Legado",
                    "situacao": "Quitado",
                    "valor": "135.00",
                    "vencimento": "2026-01-20",
                }
            ],
            "evolucao": [
                {
                    "data": "2025-05-20",
                    "faixa": "Faixa Branca Infantil",
                    "grau": "",
                    "tipo": "Início dos Treinos",
                },
                {
                    "data": "2025-06-21",
                    "faixa": "Faixa Branca Infantil",
                    "grau": "1°",
                    "tipo": "Novo Grau",
                },
            ],
            "historico": [
                {
                    "data": "06/05/2026",
                    "modalidade": "Jiu Jitsu Infanto-Juvenil",
                    "horario": "18:00 : 19:00",
                    "origem": "Check-in Tatame",
                    "professor_instrutor": "Professor",
                }
            ],
        }
        payload.update(overrides)
        return payload

    def test_fails_when_person_types_are_missing(self):
        self._seed_belt_ranks()
        self._write_student("88622-aluno-teste.json", self._base_payload())

        with self.assertRaisesMessage(CommandError, "seed_system_initial_person_type"):
            self._call_seed()

    def test_creates_dependent_guardian_relationship_and_graduations_idempotently(self):
        self._seed_person_types()
        self._seed_belt_ranks()
        self._write_student("88622-aluno-teste.json", self._base_payload())

        first_output = self._call_seed()
        second_output = self._call_seed()

        dependent = Person.objects.get(cpf="KANRI-88622")
        guardian = Person.objects.get(cpf="111.222.333-44")

        self.assertEqual(dependent.full_name, "Aluno Teste")
        self.assertEqual(dependent.person_type.code, PersonTypeCode.DEPENDENT)
        self.assertEqual(dependent.postal_code, "74672-550")
        self.assertEqual(dependent.address, "Rua do Angico")
        self.assertEqual(dependent.martial_art, "jiu_jitsu")
        self.assertEqual(dependent.martial_art_graduation, "Faixa Branca Infantil")
        self.assertEqual(dependent.martial_art_started_at, date(2025, 5, 20))
        self.assertEqual(dependent.martial_art_last_graduation_at, date(2025, 6, 21))
        self.assertEqual(dependent.jiu_jitsu_stripes, 1)

        self.assertEqual(guardian.full_name, "Responsavel Teste")
        self.assertEqual(guardian.person_type.code, PersonTypeCode.GUARDIAN)
        self.assertEqual(guardian.email, "responsavel@example.com")

        relationship = PersonRelationship.objects.get(
            source_person=guardian,
            target_person=dependent,
        )
        self.assertEqual(relationship.kinship_type, "pai")
        self.assertIn("Responsável financeiro", relationship.notes)

        graduations = Graduation.objects.filter(person=dependent).order_by("awarded_at")
        self.assertEqual(graduations.count(), 2)
        self.assertEqual(graduations[0].belt_rank.code, "kids-white")
        self.assertEqual(graduations[1].grade_number, 1)

        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(PersonRelationship.objects.count(), 1)
        self.assertEqual(Graduation.objects.count(), 2)
        self.assertIn("CPF substituto", first_output)
        self.assertIn("financeiro não importado: 1", first_output)
        self.assertIn("histórico de aulas não importado: 1", first_output)
        self.assertIn("atualizado", second_output)

    def test_uses_real_student_cpf_when_document_is_unique_and_own_document(self):
        self._seed_person_types()
        self._seed_belt_ranks()
        self._write_student(
            "77242-aluno-adulto.json",
            self._base_payload(
                nome="Aluno Adulto",
                nascimento="1980-11-06",
                tipo_documento="CPF",
                n_documento="22233344455",
                responsavel={
                    "nome": "",
                    "email": "",
                    "vinculo": "",
                    "telefone": "",
                    "tipo_documento": "",
                    "n_documento": "",
                    "observacoes": "",
                    "responsavel_financeiro": False,
                },
                evolucao=[
                    {
                        "data": "2025-01-10",
                        "faixa": "Faixa Branca",
                        "grau": "4°",
                        "tipo": "Novo Grau",
                    },
                    {
                        "data": "2025-03-10",
                        "faixa": "Faixa Azul",
                        "grau": "",
                        "tipo": "Troca de Faixa",
                    },
                ],
            ),
        )

        self._call_seed()

        student = Person.objects.get(cpf="222.333.444-55")

        self.assertEqual(student.person_type.code, PersonTypeCode.STUDENT)
        self.assertEqual(student.jiu_jitsu_belt, "blue")
        self.assertEqual(student.jiu_jitsu_stripes, 0)
        self.assertEqual(
            list(student.graduations.order_by("awarded_at").values_list("belt_rank__code", flat=True)),
            ["adult-white", "adult-blue"],
        )

    def test_cleans_placeholder_address_values(self):
        self._seed_person_types()
        self._seed_belt_ranks()
        self._write_student(
            "120166-davi-rodrigues-siqueira.json",
            self._base_payload(
                nome="Davi Rodrigues Siqueira",
                tipo_documento="CPF",
                n_documento="04561780157",
                responsavel={
                    "nome": "",
                    "email": "",
                    "vinculo": "",
                    "telefone": "",
                    "tipo_documento": "",
                    "n_documento": "",
                    "observacoes": "",
                    "responsavel_financeiro": False,
                },
                endereco={
                    "cep": "74673-050",
                    "logradouro": "Carregando...",
                    "numero": "",
                    "complemento": "Carregando...",
                    "bairro": "Carregando...",
                    "cidade": "Carregando...",
                    "uf": "Carregando...",
                },
                evolucao=[],
            ),
        )

        output = self._call_seed()

        student = Person.objects.get(cpf="045.617.801-57")
        self.assertEqual(student.postal_code, "74673-050")
        self.assertEqual(student.address, "")
        self.assertEqual(student.address_complement, "")
        self.assertEqual(student.address_neighborhood, "")
        self.assertEqual(student.city, "")
        self.assertIn("placeholder de endereço removido", output)


class SubscriptionPlanValuesSeedCommandTestCase(TestCase):
    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())

    def test_seed_system_initial_subscription_plans_values_creates_idempotent_priced_plans(self):
        self._call("seed_system_initial_subscription_plans")
        self._call("seed_system_initial_subscription_plans_values")
        self._call("seed_system_initial_subscription_plans_values")

        # PRD-127: Individual e Família migraram para PlanTier/PlanPrice (desconto
        # dinâmico). SubscriptionPlan agora só gera as linhas de Veterano (loyalty),
        # e só existe o Veterano 5x por semana (não há Veterano 2x).
        self.assertEqual(
            SubscriptionPlan.objects.exclude(code__in=("individual", "loyalty", "family")).count(),
            8,
        )
        self.assertFalse(SubscriptionPlan.objects.get(code="individual").is_active)
        self.assertFalse(SubscriptionPlan.objects.get(code="loyalty").is_active)
        self.assertFalse(SubscriptionPlan.objects.get(code="family").is_active)
        self.assertFalse(
            SubscriptionPlan.objects.filter(code__startswith="loyalty-2x").exists()
        )

        asaas_card_monthly = SubscriptionPlan.objects.get(
            code="loyalty-5x-asaas-card-monthly"
        )
        self.assertEqual(asaas_card_monthly.price, Decimal("245.00"))
        self.assertEqual(asaas_card_monthly.base_monthly_net_price, Decimal("234.00"))
        self.assertEqual(asaas_card_monthly.gateway_code, "asaas_card")
        self.assertEqual(asaas_card_monthly.gateway_percentage_fee, Decimal("0.0429"))
        self.assertEqual(asaas_card_monthly.cycle_discount_percentage, Decimal("0.0000"))
        self.assertIsNone(asaas_card_monthly.monthly_reference_price)
        self.assertTrue(asaas_card_monthly.is_loyalty_plan)

        loyalty_annual = SubscriptionPlan.objects.get(
            code="loyalty-5x-asaas-card-annual"
        )
        self.assertEqual(loyalty_annual.price, Decimal("2340.00"))
        self.assertEqual(loyalty_annual.monthly_reference_price, Decimal("195.00"))
        self.assertEqual(loyalty_annual.cycle_discount_percentage, Decimal("0.1971"))
        self.assertTrue(loyalty_annual.is_loyalty_plan)
        self.assertFalse(SubscriptionPlan.objects.filter(gateway_code="stripe_card").exists())


class PlanTierPriceSeedCommandTestCase(TestCase):
    def _call(self, command_name):
        call_command(command_name, stdout=StringIO())

    def test_seed_creates_tiers_and_prices_idempotently(self):
        self._call("seed_system_initial_plan_tiers")
        self._call("seed_system_initial_plan_prices")
        self._call("seed_system_initial_plan_tiers")
        self._call("seed_system_initial_plan_prices")

        self.assertEqual(PlanTier.objects.count(), 4)
        self.assertEqual(PlanPrice.objects.count(), 44)

        adult_2x = PlanTier.objects.get(code="adult-2x")
        self.assertEqual(adult_2x.family_discount_percentage, Decimal("0.1800"))
        self.assertEqual(adult_2x.audience, "adult")
        self.assertEqual(adult_2x.weekly_frequency, 2)

        stripe_price = PlanPrice.objects.get(
            tier=adult_2x, gateway_code="stripe_card", billing_cycle="monthly"
        )
        # PRD-127: preço sempre computado pela fórmula única (compute_gross_price),
        # sem valores manuais divergentes — R$ 229,14 é o correto para base R$ 220,00
        # com taxa Stripe de 3,99% (o antigo SubscriptionPlan gravava R$ 228,80 direto
        # do JSON, ignorando a própria fórmula do modelo).
        self.assertEqual(stripe_price.price, Decimal("229.14"))
        self.assertEqual(stripe_price.payment_method, "credit_card")

        asaas_pix_annual = PlanPrice.objects.get(
            tier__code="adult-5x", gateway_code="asaas_pix", billing_cycle="annual"
        )
        self.assertEqual(asaas_pix_annual.price, Decimal("2400.00"))

        kids_2x_price = PlanPrice.objects.get(
            tier__code="kids-2x", gateway_code="stripe_card", billing_cycle="monthly"
        )
        self.assertEqual(kids_2x_price.price, Decimal("208.31"))
        self.assertEqual(kids_2x_price.tier.audience, "kids_juvenile")

        kids_2x_asaas_pix_monthly = PlanPrice.objects.get(
            tier__code="kids-2x", gateway_code="asaas_pix", billing_cycle="monthly"
        )
        self.assertEqual(kids_2x_asaas_pix_monthly.price, Decimal("250.00"))

        # PRD-137: recorrente Stripe passou a existir também em semestral/anual
        # (antes só existia mensal) — desconto de fidelidade vs. Asaas Cartão.
        stripe_adult_2x_semiannual = PlanPrice.objects.get(
            tier__code="adult-2x", gateway_code="stripe_card", billing_cycle="semiannual"
        )
        self.assertEqual(stripe_adult_2x_semiannual.price, Decimal("1195.00"))

        stripe_adult_2x_annual = PlanPrice.objects.get(
            tier__code="adult-2x", gateway_code="stripe_card", billing_cycle="annual"
        )
        self.assertEqual(stripe_adult_2x_annual.price, Decimal("2265.00"))

        stripe_kids_5x_semiannual = PlanPrice.objects.get(
            tier__code="kids-5x", gateway_code="stripe_card", billing_cycle="semiannual"
        )
        self.assertEqual(stripe_kids_5x_semiannual.price, Decimal("1250.00"))

        stripe_kids_5x_annual = PlanPrice.objects.get(
            tier__code="kids-5x", gateway_code="stripe_card", billing_cycle="annual"
        )
        self.assertEqual(stripe_kids_5x_annual.price, Decimal("2390.00"))

    def test_seed_prices_requires_tier_to_exist(self):
        with self.assertRaises(CommandError):
            self._call("seed_system_initial_plan_prices")

    @override_settings(STRIPE_PLAN_SYNC_ENABLED=True, STRIPE_SECRET_KEY="")
    def test_seed_prices_requires_secret_key_when_sync_enabled(self):
        self._call("seed_system_initial_plan_tiers")
        with self.assertRaises(CommandError):
            self._call("seed_system_initial_plan_prices")

    @override_settings(STRIPE_PLAN_SYNC_ENABLED=True, STRIPE_SECRET_KEY="sk_test_123")
    @patch("system.services.stripe_sync.sync_plan_to_stripe")
    def test_seed_prices_syncs_only_stripe_card_rows_when_enabled(self, mock_sync):
        mock_sync.side_effect = lambda price: price
        self._call("seed_system_initial_plan_tiers")
        self._call("seed_system_initial_plan_prices")

        synced_prices = [call.args[0] for call in mock_sync.call_args_list]
        self.assertTrue(synced_prices)
        self.assertTrue(all(p.gateway_code == "stripe_card" for p in synced_prices))
        self.assertEqual(
            len(synced_prices),
            PlanPrice.objects.filter(gateway_code="stripe_card").count(),
        )


