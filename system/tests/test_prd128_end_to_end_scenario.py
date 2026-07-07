"""PRD-128: cenario N:N completo cobrindo o ciclo de vida real de uma familia.

Titular contrata (PIX) -> adiciona dependente com assinatura Stripe recorrente
propria (desconto familia aplica em ambos) -> tenta remover o dependente antes
da carencia (bloqueado, vinculo preservado) -> a carencia termina (simulada via
ORM) -> remove o dependente (permitido, desconto reverte para o titular).
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import CheckoutAction, DependentFinancialMode, PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PlanPrice,
    PlanTier,
    PortalAccount,
    PreRegistration,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod, PlanWeeklyFrequency
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.dependent_registration import finalize_dependent_registration
from system.services.plan_change import get_plan_change_lock


class FullFamilyLifecycleScenarioTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-n2n",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.TWICE,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price_pix = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.price_stripe_card = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            gateway_code="stripe_card",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.owner = Person.objects.create(
            full_name="Titular Ciclo Completo N2N",
            cpf="390.533.447-05",
            person_type=self.student_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.MALE,
            email="titular.n2n@example.com",
        )
        self.account = PortalAccount(person=self.owner)
        self.account.set_password("123456")
        self.account.save()

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    @patch("system.services.family_pricing.remove_family_discount")
    @patch("system.services.family_pricing.apply_family_discount")
    def test_contratar_aderir_bloquear_liberar_e_reverter_desconto(
        self, mocked_apply, mocked_remove
    ):
        # 1) Titular contrata via PIX (nao Stripe, nao entra em carencia).
        owner_membership = Membership.objects.create(
            person=self.owner,
            plan_price=self.price_pix,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        owner_membership.recompute_billed_price()
        owner_membership.save(update_fields=["billed_price"])
        self.assertFalse(owner_membership.family_discount_applied)
        self.assertEqual(owner_membership.billed_price, self.price_pix.price)

        # 2) Titular adiciona dependente com assinatura Stripe recorrente
        # propria (mesmo tier, gateway diferente) - o webhook ja teria
        # sincronizado o stripe_subscription_id na pre-registration.
        pre_registration = PreRegistration.objects.create(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "plan_payment": {
                    "stripe_subscription_id": "sub_n2n_dependent",
                    "stripe_subscription_item_id": "",
                },
            },
        )
        cleaned_data = {
            "dependent_name": "Dependente Ciclo Completo N2N",
            "dependent_cpf": "153.509.460-56",
            "dependent_password": "12345678",
            "dependent_biological_sex": BiologicalSex.MALE,
            "financial_mode": DependentFinancialMode.DEPENDENT_OWN,
            "selected_plan_obj": self.price_stripe_card,
            "checkout_action": CheckoutAction.STRIPE_CARD,
        }

        result = finalize_dependent_registration(
            self.owner, cleaned_data, pre_registration=pre_registration
        )
        dependent = result["dependent"]

        dependent_membership = Membership.objects.get(person=dependent)
        dependent_membership.status = MembershipStatus.ACTIVE
        dependent_membership.current_period_start = timezone.now()
        dependent_membership.current_period_end = timezone.now() + timezone.timedelta(days=30)
        dependent_membership.save(
            update_fields=["status", "current_period_start", "current_period_end"]
        )
        self.assertEqual(dependent_membership.stripe_subscription_id, "sub_n2n_dependent")
        self.assertEqual(dependent_membership.plan_price_id, self.price_stripe_card.pk)

        # Desconto familia deve aplicar em ambos (2 pessoas no mesmo tier).
        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertTrue(owner_membership.family_discount_applied)
        self.assertTrue(dependent_membership.family_discount_applied)
        expected_discounted = (self.price_pix.price * Decimal("0.82")).quantize(Decimal("0.01"))
        self.assertEqual(owner_membership.billed_price, expected_discounted)

        # 3) Titular tenta trocar de plano: catalogo de troca deve estar
        # vazio para o titular (PIX, sem carencia -> nao bloqueado, mas o
        # dependente Stripe recorrente esta dentro da carencia).
        dependent_lock = get_plan_change_lock(dependent_membership)
        self.assertTrue(dependent_lock["is_locked"])

        # 4) Titular tenta remover o dependente ANTES da carencia terminar:
        # deve ser bloqueado, vinculo preservado, desconto continua aplicado.
        self._login()
        response = self.client.post(
            reverse("system:dependent-remove", args=[dependent.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PersonRelationship.objects.filter(
                source_person=self.owner,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )
        owner_membership.refresh_from_db()
        self.assertTrue(owner_membership.family_discount_applied)

        # 5) A carencia termina (simulada via ORM).
        dependent_membership.current_period_end = timezone.now() - timezone.timedelta(days=1)
        dependent_membership.save(update_fields=["current_period_end"])
        self.assertFalse(get_plan_change_lock(dependent_membership)["is_locked"])

        # 6) Agora a remocao e permitida: vinculo apagado, desconto reverte
        # para o titular (volta a pagar o preco cheio).
        response = self.client.post(
            reverse("system:dependent-remove", args=[dependent.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            PersonRelationship.objects.filter(
                source_person=self.owner,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )
        owner_membership.refresh_from_db()
        self.assertFalse(owner_membership.family_discount_applied)
        self.assertEqual(owner_membership.billed_price, self.price_pix.price)

    def test_upgrade_titular_para_5x_nao_afeta_dependente_em_tier_diferente(self):
        """Regressao: trocar o plano do titular para outro tier nao deve
        gerar desconto familia com um dependente em tier diferente."""
        tier_5x = PlanTier.objects.create(
            code="adult-5x-n2n",
            display_name="Adulto 5x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=PlanWeeklyFrequency.FIVE_TIMES,
            family_discount_percentage=Decimal("0.18"),
        )
        price_5x_pix = PlanPrice.objects.create(
            tier=tier_5x,
            payment_method=PlanPaymentMethod.PIX,
            gateway_code="asaas_pix",
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("320.00"),
        )
        dependent = Person.objects.create(
            full_name="Dependente Tier Diferente N2N",
            cpf="153.509.460-56",
            person_type=self.student_type,
            birth_date=date(2010, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        owner_membership = Membership.objects.create(
            person=self.owner,
            plan_price=self.price_pix,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        dependent_membership = Membership.objects.create(
            person=dependent,
            plan_price=self.price_pix,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        from system.services.family_pricing import recompute_family_discounts_for_person

        recompute_family_discounts_for_person(self.owner)
        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertTrue(owner_membership.family_discount_applied)
        self.assertTrue(dependent_membership.family_discount_applied)

        # Titular faz upgrade (simulado via troca direta de plan_price).
        owner_membership.plan_price = price_5x_pix
        owner_membership.save(update_fields=["plan_price"])
        recompute_family_discounts_for_person(self.owner)

        owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertFalse(owner_membership.family_discount_applied)
        self.assertFalse(dependent_membership.family_discount_applied)
        self.assertEqual(dependent_membership.billed_price, self.price_pix.price)
