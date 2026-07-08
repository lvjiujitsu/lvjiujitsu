from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from system.models import PlanPrice, PlanTier, SubscriptionPlan
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services.stripe_sync import StripeSyncError, sync_plan_to_stripe


@override_settings(STRIPE_SECRET_KEY="sk_test_123", PAYMENT_CURRENCY="brl")
class SyncPlanToStripeSubscriptionPlanTestCase(TestCase):
    """Regressão: SubscriptionPlan (Veterano legado) continua sincronizando como antes."""

    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            code="loyalty-5x-stripe-monthly",
            display_name="Veterano 5x por semana",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("220.00"),
            gateway_percentage_fee=Decimal("0.0399"),
            description="Assinatura recorrente mensal.",
        )

    @patch("system.services.stripe_sync._get_client")
    def test_creates_product_and_price_when_absent(self, mock_get_client):
        client = MagicMock()
        client.Product.create.return_value = {"id": "prod_1"}
        client.Price.create.return_value = {"id": "price_1"}
        mock_get_client.return_value = client

        synced = sync_plan_to_stripe(self.plan)

        client.Product.create.assert_called_once()
        product_kwargs = client.Product.create.call_args.kwargs
        self.assertEqual(product_kwargs["name"], "Veterano 5x por semana")
        self.assertEqual(product_kwargs["description"], "Assinatura recorrente mensal.")
        self.assertEqual(product_kwargs["metadata"]["plan_code"], "loyalty-5x-stripe-monthly")

        price_kwargs = client.Price.create.call_args.kwargs
        self.assertEqual(price_kwargs["recurring"], {"interval": "month", "interval_count": 1})

        self.assertEqual(synced.stripe_product_id, "prod_1")
        self.assertEqual(synced.stripe_price_id, "price_1")
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.stripe_product_id, "prod_1")
        self.assertEqual(self.plan.stripe_price_id, "price_1")

    @patch("system.services.stripe_sync._get_client")
    def test_skips_zero_price_plan(self, mock_get_client):
        self.plan.base_monthly_net_price = None
        self.plan.price = Decimal("0.00")
        self.plan.save()
        client = MagicMock()
        mock_get_client.return_value = client

        sync_plan_to_stripe(self.plan)

        client.Product.create.assert_not_called()

    def test_raises_without_stripe_secret_key(self):
        with override_settings(STRIPE_SECRET_KEY=""):
            with self.assertRaises(StripeSyncError):
                sync_plan_to_stripe(self.plan)


@override_settings(STRIPE_SECRET_KEY="sk_test_123", PAYMENT_CURRENCY="brl")
class SyncPlanToStripePlanPriceTestCase(TestCase):
    """PRD-137: PlanPrice (catálogo novo) não tinha nenhum caminho de sincronização
    Stripe — sync_plan_to_stripe operava só sobre SubscriptionPlan legado."""

    def setUp(self):
        self.tier = PlanTier.objects.create(
            code="adult-2x-stripe-sync-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.SEMIANNUAL,
            base_monthly_net_price=Decimal("215.12"),
            cycle_discount_percentage=Decimal("0.1111"),
            gateway_percentage_fee=Decimal("0.0399"),
        )

    @patch("system.services.stripe_sync._get_client")
    def test_creates_product_and_price_for_plan_price(self, mock_get_client):
        client = MagicMock()
        client.Product.create.return_value = {"id": "prod_pp_1"}
        client.Price.create.return_value = {"id": "price_pp_1"}
        mock_get_client.return_value = client

        synced = sync_plan_to_stripe(self.price)

        product_kwargs = client.Product.create.call_args.kwargs
        self.assertEqual(product_kwargs["name"], "Adulto 2x por semana")
        self.assertIsNone(product_kwargs["description"])
        self.assertEqual(
            product_kwargs["metadata"]["plan_code"],
            "adult-2x-stripe-sync-test-stripe_card-semiannual",
        )

        price_kwargs = client.Price.create.call_args.kwargs
        self.assertEqual(price_kwargs["recurring"], {"interval": "month", "interval_count": 6})
        self.assertEqual(price_kwargs["unit_amount"], 119500)

        self.assertEqual(synced.stripe_product_id, "prod_pp_1")
        self.assertEqual(synced.stripe_price_id, "price_pp_1")
        self.price.refresh_from_db()
        self.assertEqual(self.price.stripe_product_id, "prod_pp_1")
        self.assertEqual(self.price.stripe_price_id, "price_pp_1")

    @patch("system.services.stripe_sync._get_client")
    def test_archives_stale_price_when_amount_changes(self, mock_get_client):
        self.price.stripe_product_id = "prod_existing"
        self.price.stripe_price_id = "price_old"
        self.price.save(update_fields=["stripe_product_id", "stripe_price_id"])

        client = MagicMock()
        client.Product.modify.return_value = {"id": "prod_existing"}
        client.Price.retrieve.return_value = {
            "id": "price_old",
            "unit_amount": 100000,
            "currency": "brl",
            "recurring": {"interval": "month", "interval_count": 6},
            "active": True,
        }
        client.Price.create.return_value = {"id": "price_new"}
        mock_get_client.return_value = client

        synced = sync_plan_to_stripe(self.price)

        client.Price.modify.assert_called_once_with("price_old", active=False)
        self.assertEqual(synced.stripe_price_id, "price_new")
        self.assertIn("price_old", synced.stripe_archived_price_ids)
