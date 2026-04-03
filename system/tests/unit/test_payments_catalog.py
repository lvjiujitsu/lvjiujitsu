from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

from system.services.payments.catalog import upsert_price_map_from_stripe_data
from system.tests.factories.finance_factories import FinancialPlanFactory
from system.tests.factories.payments_factories import StripePlanPriceMapFactory


@pytest.mark.django_db
def test_upsert_price_map_from_stripe_data_retires_previous_current_mapping():
    plan = FinancialPlanFactory()
    previous_map = StripePlanPriceMapFactory(
        plan=plan,
        stripe_price_id="price_old",
        stripe_product_id="prod_old",
        is_current=True,
        is_active=True,
        is_legacy=False,
    )
    payload = {
        "id": "price_new",
        "active": True,
        "currency": "brl",
        "unit_amount": 30000,
        "lookup_key": "plan_monthly_v2",
        "recurring": {"interval": "month", "interval_count": 1},
        "product": {"id": "prod_new", "name": "Plano Mensal Oficial"},
    }

    price_map, created = upsert_price_map_from_stripe_data(
        plan=plan,
        price_payload=payload,
        is_current=True,
        notes="Importado da conta oficial.",
    )
    previous_map.refresh_from_db()

    assert created is True
    assert price_map.is_current is True
    assert price_map.is_active is True
    assert price_map.is_legacy is False
    assert price_map.product_name == "Plano Mensal Oficial"
    assert previous_map.is_current is False
    assert previous_map.is_active is False
    assert previous_map.is_legacy is True
    assert previous_map.valid_until is not None


@pytest.mark.django_db
def test_upsert_price_map_from_stripe_data_requires_recurring_price():
    plan = FinancialPlanFactory()
    payload = {
        "id": "price_single_charge",
        "active": True,
        "currency": "brl",
        "unit_amount": 15000,
        "product": {"id": "prod_single", "name": "Taxa avulsa"},
    }

    with pytest.raises(ValidationError):
        upsert_price_map_from_stripe_data(plan=plan, price_payload=payload)


@pytest.mark.django_db
def test_import_stripe_price_map_command_fetches_price_and_updates_local_mapping(monkeypatch):
    plan = FinancialPlanFactory(slug="mensal")
    payload = {
        "id": "price_cmd_001",
        "active": True,
        "currency": "brl",
        "unit_amount": 25000,
        "lookup_key": "mensal_oficial",
        "recurring": {"interval": "month", "interval_count": 1},
        "product": {"id": "prod_cmd_001", "name": "Mensal Cartao de Credito Stripe"},
    }
    mirror_calls = []

    class FakePriceApi:
        @staticmethod
        def retrieve(price_id, expand):
            assert price_id == "price_cmd_001"
            assert expand == ["product"]
            return payload

    class FakeStripeSdk:
        Price = FakePriceApi

    monkeypatch.setattr(
        "system.management.commands.import_stripe_price_map.get_stripe_sdk",
        lambda: FakeStripeSdk(),
    )
    monkeypatch.setattr(
        "system.management.commands.import_stripe_price_map.sync_price_payload",
        lambda data: mirror_calls.append(data) or None,
    )

    stdout = StringIO()
    call_command(
        "import_stripe_price_map",
        plan_slug=plan.slug,
        price_id="price_cmd_001",
        is_current=True,
        stdout=stdout,
    )

    price_map = plan.stripe_price_maps.get(stripe_price_id="price_cmd_001")

    assert mirror_calls == [payload]
    assert price_map.is_current is True
    assert price_map.product_name == "Mensal Cartao de Credito Stripe"
    assert "Mapeamento criado" in stdout.getvalue()
