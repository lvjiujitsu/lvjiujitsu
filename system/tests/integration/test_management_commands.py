from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from system.constants import ROLE_ADMIN_MASTER
from system.models import (
    AcademyConfiguration,
    ConsentTerm,
    FinancialPlan,
    NoticeBoardMessage,
    PdvProduct,
    PublicClassSchedule,
    PublicPlan,
    StripePlanPriceMap,
    SystemUser,
)


@pytest.mark.django_db
def test_criar_superuser_admin_creates_or_updates_admin_user(monkeypatch):
    monkeypatch.setenv("DJANGO_ADMIN_CPF", "12345678909")
    monkeypatch.setenv("DJANGO_ADMIN_FULL_NAME", "Admin Seed")
    monkeypatch.setenv("DJANGO_ADMIN_EMAIL", "admin.seed@example.com")
    monkeypatch.setenv("DJANGO_ADMIN_PASSWORD", "admin123")
    call_command("criar_superuser_admin")

    user = SystemUser.objects.get(cpf="12345678909")

    assert user.is_superuser is True
    assert user.is_staff is True
    assert user.full_name == "Admin Seed"
    assert user.has_role(ROLE_ADMIN_MASTER) is True


@pytest.mark.django_db
def test_initial_seeds_populates_core_catalog(tmp_path, settings):
    control_file = tmp_path / "critical_exports.flag"
    settings.CRITICAL_EXPORT_CONTROL_FILE = str(control_file)

    call_command("initial_seeds")

    configuration = AcademyConfiguration.objects.get(singleton_key="default")

    assert configuration.hero_title == "LV Culture of Martial Arts"
    assert PublicPlan.objects.filter(name="Plano Mensal").exists()
    assert PublicClassSchedule.objects.filter(class_level__icontains="Turma Noturna 19h").exists()
    assert FinancialPlan.objects.filter(slug="mensal-recorrente-stripe").exists()
    assert StripePlanPriceMap.objects.filter(stripe_price_id="price_1SnllzHDywrdzSUoHLdZvLsK").exists()
    assert PdvProduct.objects.filter(sku="FAIXA-LV").exists()
    assert ConsentTerm.objects.filter(code="privacy_policy", version=2, is_active=True).exists()
    assert NoticeBoardMessage.objects.filter(title="Base inicial sincronizada com a vitrine publica").exists()
    assert Path(settings.CRITICAL_EXPORT_CONTROL_FILE).read_text(encoding="utf-8") == "EXPORT_ALLOWED=1\n"
