"""PRD-130: troca de plano (upgrade/downgrade) migrada para o catálogo
PlanTier/PlanPrice. Regressão reportada pelo usuário: "Trocar plano" sumiu da
home porque build_plan_catalog/get_eligible_plans só liam SubscriptionPlan, e
as linhas não-veteranas desse modelo foram inativadas pela PRD-127.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
    RegistrationOrder,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.plan_change import (
    apply_plan_change,
    build_plan_catalog,
    calculate_plan_change,
    create_plan_change_order,
    get_last_paid_order_for_plan,
)
from system.services.registration_checkout import (
    CATALOG_ID_PREFIX_PLAN_PRICE,
    build_catalog_plan_id,
)


def pp_id(pk):
    return build_catalog_plan_id(CATALOG_ID_PREFIX_PLAN_PRICE, pk)


class BuildPlanCatalogPlanPriceTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier_2x = PlanTier.objects.create(
            code="adult-2x-catalog-test",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.tier_5x = PlanTier.objects.create(
            code="adult-5x-catalog-test",
            display_name="Adulto 5x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price_2x_pix = PlanPrice.objects.create(
            tier=self.tier_2x,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.price_5x_pix = PlanPrice.objects.create(
            tier=self.tier_5x,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("300.00"),
        )
        self.person = Person.objects.create(
            full_name="Aluno Troca Plan Price",
            cpf="153.509.460-56",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.account = PortalAccount(person=self.person)
        self.account.set_password("123456")
        self.account.save()
        now = timezone.now()
        self.membership = Membership.objects.create(
            person=self.person,
            plan_price=self.price_2x_pix,
            status=MembershipStatus.ACTIVE,
            current_period_start=now - timedelta(days=15),
            current_period_end=now + timedelta(days=15),
        )
        RegistrationOrder.objects.create(
            person=self.person,
            plan_price_ref=self.price_2x_pix,
            plan_price=self.price_2x_pix.price,
            total=self.price_2x_pix.price,
            payment_status="paid",
            paid_at=now - timedelta(days=15),
        )

    def test_catalog_is_not_empty_for_plan_price_membership(self):
        catalog = build_plan_catalog(self.person, self.membership)

        self.assertTrue(catalog, "catálogo de troca não deveria estar vazio")
        by_id = {item["id"]: item for item in catalog}
        self.assertIn(pp_id(self.price_5x_pix.pk), by_id)
        self.assertFalse(by_id[pp_id(self.price_5x_pix.pk)]["is_current"])

        # o plano atual aparece no catálogo, marcado como "atual" (não trocável para ele mesmo)
        self.assertIn(pp_id(self.price_2x_pix.pk), by_id)
        self.assertTrue(by_id[pp_id(self.price_2x_pix.pk)]["is_current"])

    def test_current_plan_card_matches_its_own_filters(self):
        """Regressão reportada pelo usuário: selecionar o filtro exato do plano
        atual (frequência/ciclo/forma de pagamento) não mostrava nada — o
        cliente esperava ver o próprio plano marcado como "Plano atual"."""
        catalog = build_plan_catalog(self.person, self.membership)
        current = next(item for item in catalog if item["is_current"])

        self.assertEqual(current["weekly_frequency"], self.price_2x_pix.weekly_frequency)
        self.assertEqual(current["billing_cycle"], self.price_2x_pix.billing_cycle)
        self.assertEqual(current["payment_method"], self.price_2x_pix.payment_method)
        self.assertFalse(current["proration"]["is_upgrade"])
        self.assertFalse(current["proration"]["has_leftover"])

    def test_home_shows_plan_change_button_for_plan_price_membership(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["plan_change_catalog"])
        self.assertContains(response, "js-open-plan-change-modal")

    def test_calculate_plan_change_between_plan_prices(self):
        proration = calculate_plan_change(self.membership, self.price_5x_pix)

        self.assertEqual(proration["new_plan"], self.price_5x_pix)
        self.assertTrue(proration["is_upgrade"])
        self.assertGreater(proration["additional_charge"], Decimal("0"))

    def test_apply_plan_change_switches_membership_to_new_plan_price(self):
        proration = calculate_plan_change(self.membership, self.price_5x_pix)
        create_plan_change_order(self.person, self.membership, self.price_5x_pix, proration)

        apply_plan_change(None, self.membership, self.price_5x_pix, proration=proration)

        self.membership.refresh_from_db()
        self.assertEqual(self.membership.plan_price_id, self.price_5x_pix.pk)
        self.assertIsNone(self.membership.plan_id)

    def test_get_last_paid_order_for_plan_price(self):
        order = get_last_paid_order_for_plan(self.person, self.price_2x_pix)

        self.assertIsNotNone(order)
        self.assertEqual(order.plan_price_ref_id, self.price_2x_pix.pk)

    def test_plan_change_select_view_switches_plan_price(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

        response = self.client.post(
            reverse("system:plan-change-select"),
            data={"selected_plan": pp_id(self.price_5x_pix.pk)},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("/pagamentos/", payload.get("redirect_url", ""))
