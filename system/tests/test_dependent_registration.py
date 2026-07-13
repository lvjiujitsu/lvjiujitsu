from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import CheckoutAction, DependentCardStrategy, DependentFinancialMode, PersonTypeCode
from system.forms.dependent_forms import DependentRegistrationForm
from system.services.dependent_registration import finalize_dependent_registration
from system.services.registration_checkout import (
    CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN,
    build_catalog_plan_id,
    create_pre_registration_plan_payment,
)
from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassGroup,
    IbjjfAgeCategory,
    BeltRank,
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
    PreRegistrationStatus,
    Product,
    ProductCategory,
    ProductVariant,
    RegistrationOrder,
    SubscriptionPlan,
)
from system.models.plan import BillingCycle, PlanAudience, PlanPaymentMethod
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.registration_checkout import parse_selected_plan_payload


def sp_id(plan_pk):
    return build_catalog_plan_id(CATALOG_ID_PREFIX_SUBSCRIPTION_PLAN, plan_pk)


class DependentRegistrationFlowTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        PersonType.objects.create(
            code=PersonTypeCode.DEPENDENT,
            display_name="Dependente",
        )
        self.owner = Person.objects.create(
            full_name="Titular Dependente Posterior",
            cpf="390.533.447-05",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            email="titular@example.com",
        )
        self.account = PortalAccount(person=self.owner)
        self.account.set_password("123456")
        self.account.save()
        self.category = ClassCategory.objects.create(
            code="adult-dependents",
            display_name="Adulto Dependentes",
            audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-dependents",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            display_order=1,
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Jiu Jitsu Noite",
            class_category=self.category,
        )
        BeltRank.objects.create(
            code="adult-white",
            display_name="Branca Adulto Dependente",
            audience=CategoryAudience.ADULT,
            color_hex="#ffffff",
            display_order=1,
        )
        BeltRank.objects.create(
            code="adult-coral-redwhite",
            display_name="Coral Adulto Dependente",
            audience=CategoryAudience.ADULT,
            color_hex="#ffffff",
            display_order=50,
        )
        self.family_plan = SubscriptionPlan.objects.create(
            code="family-dependent",
            display_name="Familiar 2x",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("299.00"),
            is_family_plan=True,
        )
        self.individual_plan = SubscriptionPlan.objects.create(
            code="individual-dependent",
            display_name="Individual 2x",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("199.00"),
            gateway_code="stripe_card",
        )
        self.product_category = ProductCategory.objects.create(
            code="dependent-materials",
            display_name="Materiais dependente",
        )
        self.product = Product.objects.create(
            sku="DEPENDENT-MATERIAL-1",
            display_name="Kimono Dependente Teste",
            category=self.product_category,
            unit_price=Decimal("350.00"),
        )
        self.product_variant = ProductVariant.objects.create(
            product=self.product,
            size="M",
            color="Azul",
            stock_quantity=3,
        )

    def test_login_required(self):
        response = self.client.get(reverse("system:dependent-add"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("system:login"), response["Location"])

    def test_direct_authenticated_get_redirects_to_home_modal(self):
        self._login()

        response = self.client.get(reverse("system:dependent-add"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('system:home')}?dependent_modal=1",
        )

    def test_family_plan_creates_active_dependent_relationship(self):
        self._login()
        Membership.objects.create(
            person=self.owner,
            plan=self.family_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
            activated_at=timezone.now(),
        )

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(use_family_plan="on"),
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("system:home"))
        dependent = Person.objects.get(cpf="529.982.247-25")
        self.assertTrue(dependent.is_active)
        self.assertTrue(dependent.access_account.is_active)
        self.assertTrue(
            PersonRelationship.objects.filter(
                source_person=self.owner,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )
        self.assertTrue(
            dependent.class_enrollments.filter(class_group=self.class_group).exists()
        )
        self.assertEqual(dependent.graduations.get().belt_rank.code, "adult-white")

    def test_paid_plan_creates_pre_registration_without_person(self):
        self._login()

        with patch(
            "system.services.dependent_registration.create_pre_registration_plan_payment"
        ) as mocked_payment:
            mocked_payment.return_value = "https://checkout.stripe.test/session"
            response = self.client.post(
                reverse("system:dependent-add"),
                data=self._payload(
                    use_family_plan="",
                    selected_plan=sp_id(self.individual_plan.pk),
                    checkout_action=CheckoutAction.STRIPE_CARD,
                ),
                follow=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://checkout.stripe.test/session")
        self.assertFalse(Person.objects.filter(cpf="529.982.247-25").exists())
        pre_registration = PreRegistration.objects.get()
        self.assertEqual(pre_registration.status, PreRegistrationStatus.AWAITING_PAYMENT)
        self.assertEqual(
            pre_registration.form_snapshot["flow_kind"],
            "dependent_addition",
        )
        self.assertEqual(
            pre_registration.form_snapshot["owner_person_id"],
            self.owner.pk,
        )
        mocked_payment.assert_called_once()

    def test_family_upgrade_creates_pre_registration_without_person(self):
        self._login()
        Membership.objects.create(
            person=self.owner,
            plan=self.individual_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
            activated_at=timezone.now(),
        )

        with patch(
            "system.services.dependent_registration.create_pre_registration_plan_payment"
        ) as mocked_payment:
            mocked_payment.return_value = "https://checkout.stripe.test/family"
            response = self.client.post(
                reverse("system:dependent-add"),
                data=self._payload(
                    financial_mode="family_upgrade",
                    selected_plan=sp_id(self.family_plan.pk),
                    checkout_action=CheckoutAction.STRIPE_CARD,
                ),
                follow=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://checkout.stripe.test/family")
        self.assertFalse(Person.objects.filter(cpf="529.982.247-25").exists())
        pre_registration = PreRegistration.objects.get()
        self.assertEqual(pre_registration.selected_plan, self.family_plan)
        self.assertEqual(
            pre_registration.form_snapshot["financial_mode"],
            "family_upgrade",
        )
        self.assertEqual(
            pre_registration.form_snapshot["selected_plans_payload"],
            [
                {
                    "person": "owner",
                    "label": "Titular Dependente Posterior + Dependente Posterior",
                    "plan_id": sp_id(self.family_plan.pk),
                }
            ],
        )
        self.assertEqual(
            parse_selected_plan_payload(pre_registration.form_snapshot),
            [
                {
                    "plan_id": sp_id(self.family_plan.pk),
                    "label": "Titular Dependente Posterior + Dependente Posterior",
                }
            ],
        )
        mocked_payment.assert_called_once()

    def test_payment_success_returns_to_dependent_flow(self):
        self._login()
        pre_registration = PreRegistration.objects.create(
            session_key=self.client.session.session_key or "",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.individual_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.AWAITING_PAYMENT,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plan": sp_id(self.individual_plan.pk),
                "plan_payment": {"stripe_session_id": "cs_test_dependent"},
            },
        )

        response = self.client.get(
            reverse("system:payment-success"),
            {
                "pre_registration_id": pre_registration.pk,
                "stage": "plan",
                "session_id": "cs_test_dependent",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('system:home')}?dependent_modal=1",
        )
        pre_registration.refresh_from_db()
        self.assertEqual(pre_registration.status, PreRegistrationStatus.PAYMENT_CONFIRMED)
        self.assertTrue(pre_registration.form_snapshot["plan_paid"])

    def test_paid_resume_finalizes_with_paid_plan_even_if_post_is_tampered(self):
        self._login()
        pre_registration = PreRegistration.objects.create(
            session_key=self.client.session.session_key or "",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.individual_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plan": sp_id(self.individual_plan.pk),
                "plan_paid": True,
            },
        )
        session = self.client.session
        session["pending_dependent_pre_registration_id"] = pre_registration.pk
        session.save()

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(
                selected_plan=sp_id(self.family_plan.pk),
                checkout_action=CheckoutAction.PAY_LATER,
            ),
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        dependent = Person.objects.get(cpf="529.982.247-25")
        order = dependent.registration_orders.get()
        self.assertEqual(order.plan, self.individual_plan)
        self.assertEqual(order.payment_status, "paid")

    def test_paid_family_upgrade_finalizes_with_owner_family_membership(self):
        self._login()
        Membership.objects.create(
            person=self.owner,
            plan=self.individual_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
            activated_at=timezone.now(),
        )
        pre_registration = PreRegistration.objects.create(
            session_key=self.client.session.session_key or "",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.family_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plan": sp_id(self.family_plan.pk),
                "financial_mode": "family_upgrade",
                "plan_paid": True,
            },
        )
        session = self.client.session
        session["pending_dependent_pre_registration_id"] = pre_registration.pk
        session.save()

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(
                financial_mode="family_upgrade",
                selected_plan=sp_id(self.family_plan.pk),
                checkout_action=CheckoutAction.STRIPE_CARD,
            ),
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        dependent = Person.objects.get(cpf="529.982.247-25")
        self.assertEqual(dependent.registration_orders.count(), 0)
        owner_order = RegistrationOrder.objects.get(
            person=self.owner,
            plan=self.family_plan,
            payment_status="paid",
        )
        self.assertEqual(owner_order.total, self.family_plan.price)
        owner_membership = (
            Membership.objects.filter(person=self.owner)
            .exclude(status=MembershipStatus.CANCELED)
            .order_by("-created_at")
            .first()
        )
        self.assertIsNotNone(owner_membership)
        self.assertEqual(owner_membership.plan, self.family_plan)
        self.assertEqual(Membership.objects.filter(person=dependent).count(), 0)

    def test_dependent_own_plan_rejects_family_plan(self):
        self._login()

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(
                financial_mode="dependent_own",
                selected_plan=sp_id(self.family_plan.pk),
                checkout_action=CheckoutAction.STRIPE_CARD,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Plano familiar deve ser selecionado como upgrade do titular.",
        )

    def test_dependent_own_plan_rejects_loyalty_plan(self):
        self._login()
        loyalty_plan = SubscriptionPlan.objects.create(
            code="loyalty-dependent",
            display_name="Veterano 2x",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("149.00"),
            is_loyalty_plan=True,
        )

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(
                financial_mode="dependent_own",
                selected_plan=sp_id(loyalty_plan.pk),
                checkout_action=CheckoutAction.STRIPE_CARD,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Plano veterano exige elegibilidade aprovada pela gestão.",
        )

    def test_family_existing_rejects_owner_without_family_membership(self):
        self._login()

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(
                financial_mode="family_existing",
                use_family_plan="on",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Não há plano familiar ativo para cobrir este dependente.",
        )

    def test_product_catalog_renders_in_dependent_wizard(self):
        self._login()

        response = self.client.get(reverse("system:dependent-add"), {"modal": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertContains(response, "dependent-page--modal")
        self.assertContains(response, 'action="/dependents/add/?modal=1"')
        self.assertContains(response, "Materiais e equipamentos")
        self.assertContains(response, "Kimono Dependente Teste")
        self.assertContains(response, "Azul")

    def test_dependent_plan_step_is_filter_first_without_financial_mode_cards(self):
        self._login()

        response = self.client.get(reverse("system:dependent-add"), {"modal": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano do dependente")
        self.assertContains(response, "Escolha frequência e período")
        self.assertContains(response, 'id="id_financial_mode"')
        self.assertContains(response, 'id="id_selected_plan"')
        self.assertNotContains(response, "Condição financeira")
        self.assertNotContains(response, 'data-financial-mode="family_existing"')
        self.assertNotContains(response, 'data-financial-mode="family_upgrade"')
        self.assertNotContains(response, 'data-financial-mode="dependent_own"')

    def test_ibjjf_categories_and_review_step_render_in_dependent_wizard(self):
        self._login()

        response = self.client.get(reverse("system:dependent-add"), {"modal": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="dep-ibjjf-json"')
        self.assertContains(response, "adult-dependents")
        self.assertContains(response, 'data-step="7"')
        self.assertContains(response, "Revisar e confirmar")

    def test_modal_invalid_post_renders_errors_inside_modal(self):
        self._login()

        response = self.client.post(
            f"{reverse('system:dependent-add')}?modal=1",
            data={"_modal": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dependent-page--modal")
        self.assertContains(response, 'action="/dependents/add/?modal=1"')
        self.assertContains(response, 'name="_modal" value="1"')

    def test_materials_selected_after_plan_payment_redirects_to_materials_payment(self):
        self._login()
        pre_registration = PreRegistration.objects.create(
            session_key=self.client.session.session_key or "",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.individual_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plan": sp_id(self.individual_plan.pk),
                "plan_paid": True,
            },
        )
        session = self.client.session
        session["pending_dependent_pre_registration_id"] = pre_registration.pk
        session.save()

        with patch(
            "system.services.dependent_registration.create_pre_registration_materials_payment"
        ) as mocked_payment:
            mocked_payment.return_value = "https://asaas.test/materials"
            response = self.client.post(
                reverse("system:dependent-add"),
                data=self._payload(
                    selected_plan=sp_id(self.individual_plan.pk),
                    checkout_action=CheckoutAction.STRIPE_CARD,
                    materials_checkout_action=CheckoutAction.PIX,
                    **{f"material_variant_{self.product_variant.pk}": "2"},
                ),
                follow=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://asaas.test/materials")
        self.assertFalse(Person.objects.filter(cpf="529.982.247-25").exists())
        mocked_payment.assert_called_once()
        pre_registration.refresh_from_db()
        self.assertEqual(
            pre_registration.form_snapshot["selected_products_payload"],
            [{"variant_id": self.product_variant.pk, "quantity": 2}],
        )

    def test_materials_success_returns_to_dependent_flow(self):
        self._login()
        pre_registration = PreRegistration.objects.create(
            session_key=self.client.session.session_key or "",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.individual_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plan": sp_id(self.individual_plan.pk),
                "plan_paid": True,
                "materials_payment": {"asaas_payment_id": "pay_dep_materials"},
            },
        )

        response = self.client.get(
            reverse("system:payment-success"),
            {
                "pre_registration_id": pre_registration.pk,
                "stage": "materials",
                "id": "pay_dep_materials",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('system:home')}?dependent_modal=1",
        )
        pre_registration.refresh_from_db()
        self.assertTrue(pre_registration.form_snapshot["materials_paid"])
        self.assertEqual(
            self.client.session["pending_dependent_pre_registration_id"],
            pre_registration.pk,
        )

    def test_modal_family_plan_completion_returns_modal_done(self):
        self._login()
        Membership.objects.create(
            person=self.owner,
            plan=self.family_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
            activated_at=timezone.now(),
        )

        response = self.client.post(
            f"{reverse('system:dependent-add')}?modal=1",
            data=self._payload(use_family_plan="on"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dependent-modal-done")
        self.assertEqual(Person.objects.filter(cpf="529.982.247-25").count(), 1)

    def test_paid_resume_with_materials_paid_finalizes_once(self):
        self._login()
        pre_registration = PreRegistration.objects.create(
            session_key=self.client.session.session_key or "",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.individual_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.PAYMENT_CONFIRMED,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plan": sp_id(self.individual_plan.pk),
                "plan_paid": True,
                "materials_paid": True,
            },
        )
        session = self.client.session
        session["pending_dependent_pre_registration_id"] = pre_registration.pk
        session.save()
        payload = self._payload(
            selected_plan=sp_id(self.individual_plan.pk),
            checkout_action=CheckoutAction.STRIPE_CARD,
        )

        first = self.client.post(reverse("system:dependent-add"), data=payload)
        second = self.client.post(reverse("system:dependent-add"), data=payload)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Person.objects.filter(cpf="529.982.247-25").count(), 1)
        dependent = Person.objects.get(cpf="529.982.247-25")
        self.assertTrue(
            PersonRelationship.objects.filter(
                source_person=self.owner,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )

    def test_same_owner_pending_pre_registration_blocks_duplicate_cpf(self):
        self._login()
        PreRegistration.objects.create(
            session_key="other-session",
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.individual_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            status=PreRegistrationStatus.AWAITING_PAYMENT,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "dependent_cpf": "529.982.247-25",
                "selected_plan": sp_id(self.individual_plan.pk),
            },
        )

        with patch("system.services.dependent_registration.create_pre_registration_plan_payment") as mocked_payment:
            response = self.client.post(
                reverse("system:dependent-add"),
                data=self._payload(
                    selected_plan=sp_id(self.individual_plan.pk),
                    checkout_action=CheckoutAction.STRIPE_CARD,
                ),
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Já existe um pré-cadastro pendente para este CPF.",
        )
        mocked_payment.assert_not_called()

    def test_existing_owned_dependent_submission_is_idempotent(self):
        self._login()
        dependent_type = PersonType.objects.get(code=PersonTypeCode.DEPENDENT)
        dependent = Person.objects.create(
            full_name="Dependente Posterior",
            cpf="529.982.247-25",
            person_type=dependent_type,
            birth_date=date(2000, 1, 1),
            biological_sex=BiologicalSex.MALE,
            is_active=True,
        )
        account = PortalAccount(person=dependent, is_active=True)
        account.set_password("12345678")
        account.save()
        PersonRelationship.objects.create(
            source_person=self.owner,
            target_person=dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

        response = self.client.post(
            reverse("system:dependent-add"),
            data=self._payload(
                selected_plan=sp_id(self.individual_plan.pk),
                checkout_action=CheckoutAction.STRIPE_CARD,
            ),
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("system:home"))
        self.assertEqual(Person.objects.filter(cpf="529.982.247-25").count(), 1)

    def _payload(self, **overrides):
        payload = {
            "dependent_name": "Dependente Posterior",
            "dependent_cpf": "529.982.247-25",
            "dependent_birthdate": "01/01/2000",
            "dependent_biological_sex": BiologicalSex.MALE,
            "dependent_email": "dependente@example.com",
            "dependent_phone": "(11) 99999-0000",
            "dependent_password": "12345678",
            "dependent_password_confirm": "12345678",
            "dependent_kinship_type": "other",
            "dependent_kinship_other_label": "Familiar",
            "dependent_class_groups": [str(self.class_group.pk)],
            "dependent_blood_type": "",
            "dependent_allergies": "",
            "dependent_injuries": "",
            "dependent_emergency_contact": "Contato Emergencia",
            "dependent_has_martial_art": "yes",
            "dependent_martial_art": "jiu_jitsu",
            "dependent_martial_art_graduation": "",
            "dependent_jiu_jitsu_belt": "white",
            "dependent_jiu_jitsu_stripes": "0",
            "dependent_martial_art_started_at": "01/01/2024",
            "dependent_martial_art_last_graduation_at": "",
            "dependent_previous_academy": "Academia Exemplo",
            "use_family_plan": "",
            "selected_plan": "",
            "checkout_action": CheckoutAction.PAY_LATER,
            "materials_checkout_action": CheckoutAction.PAY_LATER,
        }
        payload.update(overrides)
        return payload

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()


class DependentCardStrategyTestCase(TestCase):
    def setUp(self):
        self.person_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.owner = Person.objects.create(
            full_name="Titular Estrategia Cartao",
            cpf="390.533.447-05",
            person_type=self.person_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            email="titular.cartao@example.com",
        )
        self.dependent_plan = SubscriptionPlan.objects.create(
            code="plan-dependent-card-strategy",
            display_name="Plano Dependente Estrategia",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price=Decimal("120.00"),
            gateway_code="stripe_card",
            stripe_price_id="price_dependent_card_strategy",
        )

    def test_card_strategy_merged_rejected_without_owner_stripe_subscription(self):
        form = DependentRegistrationForm(owner=self.owner)
        form.cleaned_data = {}
        cleaned_data = {
            "financial_mode": DependentFinancialMode.DEPENDENT_OWN,
            "checkout_action": CheckoutAction.STRIPE_CARD,
            "card_strategy": DependentCardStrategy.SAME_CARD_MERGED,
        }

        form._clean_card_strategy(cleaned_data)

        self.assertIn("card_strategy", form.errors)
        self.assertEqual(cleaned_data["card_strategy"], DependentCardStrategy.NEW_CARD)

    def test_card_strategy_merged_accepted_with_owner_stripe_subscription(self):
        Membership.objects.create(
            person=self.owner,
            plan=self.dependent_plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_owner_active_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        form = DependentRegistrationForm(owner=self.owner)
        cleaned_data = {
            "financial_mode": DependentFinancialMode.DEPENDENT_OWN,
            "checkout_action": CheckoutAction.STRIPE_CARD,
            "card_strategy": DependentCardStrategy.SAME_CARD_MERGED,
        }

        form._clean_card_strategy(cleaned_data)

        self.assertEqual(form.errors, {})
        self.assertEqual(cleaned_data["card_strategy"], DependentCardStrategy.SAME_CARD_MERGED)

    def test_card_strategy_defaults_to_new_card_outside_dependent_own_stripe_flow(self):
        form = DependentRegistrationForm(owner=self.owner)
        cleaned_data = {
            "financial_mode": DependentFinancialMode.FAMILY_EXISTING,
            "checkout_action": CheckoutAction.PAY_LATER,
            "card_strategy": DependentCardStrategy.SAME_CARD_MERGED,
        }

        form._clean_card_strategy(cleaned_data)

        self.assertEqual(form.errors, {})
        self.assertEqual(cleaned_data["card_strategy"], DependentCardStrategy.NEW_CARD)

    def test_create_pre_registration_plan_payment_merges_into_owner_subscription(self):
        Membership.objects.create(
            person=self.owner,
            plan=self.dependent_plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_owner_merge_1",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        pre_registration = PreRegistration.objects.create(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plans_payload": [
                    {"person": "dependent", "label": "Dependente", "plan_id": self.dependent_plan.pk}
                ],
            },
        )

        with patch(
            "system.services.stripe_checkout.merge_plan_into_existing_subscription"
        ) as mocked_merge:
            mocked_merge.return_value = {
                "stripe_subscription_id": "sub_owner_merge_1",
                "stripe_subscription_item_id": "si_new_dependent_item",
            }
            checkout_url = create_pre_registration_plan_payment(
                pre_registration,
                CheckoutAction.STRIPE_CARD,
                card_strategy=DependentCardStrategy.SAME_CARD_MERGED,
                owner=self.owner,
            )

        mocked_merge.assert_called_once()
        self.assertIn("stage=plan", checkout_url)
        self.assertIn(f"pre_registration_id={pre_registration.pk}", checkout_url)
        pre_registration.refresh_from_db()
        plan_payment = pre_registration.form_snapshot["plan_payment"]
        self.assertTrue(plan_payment["merged_into_owner_subscription"])
        self.assertEqual(plan_payment["stripe_subscription_id"], "sub_owner_merge_1")
        self.assertEqual(plan_payment["stripe_subscription_item_id"], "si_new_dependent_item")

    def test_finalize_dependent_registration_syncs_stripe_ids_from_snapshot(self):
        pre_registration = PreRegistration.objects.create(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            selected_plan=self.dependent_plan,
            checkout_action=CheckoutAction.STRIPE_CARD,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "plan_payment": {
                    "stripe_subscription_id": "sub_owner_merge_1",
                    "stripe_subscription_item_id": "si_new_dependent_item",
                },
            },
        )
        cleaned_data = {
            "dependent_name": "Dependente Sincronizado",
            "dependent_cpf": "153.509.460-56",
            "dependent_password": "12345678",
            "dependent_biological_sex": BiologicalSex.MALE,
            "financial_mode": DependentFinancialMode.DEPENDENT_OWN,
            "selected_plan_obj": self.dependent_plan,
            "checkout_action": CheckoutAction.STRIPE_CARD,
        }

        result = finalize_dependent_registration(
            self.owner, cleaned_data, pre_registration=pre_registration
        )

        dependent = result["dependent"]
        membership = Membership.objects.get(person=dependent)
        self.assertEqual(membership.stripe_subscription_id, "sub_owner_merge_1")
        self.assertEqual(membership.stripe_subscription_item_id, "si_new_dependent_item")

    def test_create_pre_registration_plan_payment_staggers_billing_cycle_anchor(self):
        owner_period_end = timezone.now() + timezone.timedelta(days=10)
        Membership.objects.create(
            person=self.owner,
            plan=self.dependent_plan,
            status=MembershipStatus.ACTIVE,
            stripe_subscription_id="sub_owner_stagger_1",
            current_period_start=timezone.now(),
            current_period_end=owner_period_end,
        )
        pre_registration = PreRegistration.objects.create(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
                "selected_plans_payload": [
                    {"person": "dependent", "label": "Dependente", "plan_id": self.dependent_plan.pk}
                ],
            },
        )

        with patch(
            "system.services.stripe_checkout.create_subscription_session_for_pre_registration"
        ) as mocked_session:
            mocked_session.return_value = {"url": "https://checkout.stripe.test/staggered"}
            checkout_url = create_pre_registration_plan_payment(
                pre_registration,
                CheckoutAction.STRIPE_CARD,
                card_strategy=DependentCardStrategy.SAME_CARD_STAGGERED,
                owner=self.owner,
            )

        self.assertEqual(checkout_url, "https://checkout.stripe.test/staggered")
        mocked_session.assert_called_once()
        _, kwargs = mocked_session.call_args
        expected_anchor = int((owner_period_end + timezone.timedelta(hours=4)).timestamp())
        self.assertEqual(kwargs["billing_cycle_anchor"], expected_anchor)


class PlanPriceDependentRegistrationTestCase(TestCase):
    """PRD-127: dependente escolhe um plano do novo catálogo PlanTier/PlanPrice
    (sem card 'Família' separado) e o desconto familiar é aplicado
    automaticamente quando o titular compartilha o mesmo tier."""

    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        PersonType.objects.create(
            code=PersonTypeCode.DEPENDENT,
            display_name="Dependente",
        )
        self.owner = Person.objects.create(
            full_name="Titular Plan Price E2E",
            cpf="390.533.447-05",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            email="titular.pp@example.com",
        )
        self.account = PortalAccount(person=self.owner)
        self.account.set_password("123456")
        self.account.save()
        self.category = ClassCategory.objects.create(
            code="adult-pp-e2e",
            display_name="Adulto PP E2E",
            audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-pp-e2e",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            display_order=1,
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Jiu Jitsu Noite PP",
            class_category=self.category,
        )
        BeltRank.objects.create(
            code="adult-white-pp-e2e",
            display_name="Branca Adulto PP E2E",
            audience=CategoryAudience.ADULT,
            color_hex="#ffffff",
            display_order=1,
        )
        self.tier = PlanTier.objects.create(
            code="adult-2x-e2e",
            display_name="Adulto 2x por semana",
            audience=PlanAudience.ADULT,
            weekly_frequency=2,
            family_discount_percentage=Decimal("0.18"),
        )
        self.price = PlanPrice.objects.create(
            tier=self.tier,
            payment_method=PlanPaymentMethod.PIX,
            billing_cycle=BillingCycle.MONTHLY,
            base_monthly_net_price=Decimal("200.00"),
        )
        self.owner_membership = Membership.objects.create(
            person=self.owner,
            plan_price=self.price,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

    def _payload(self, **overrides):
        payload = {
            "dependent_name": "Dependente Plan Price",
            "dependent_cpf": "529.982.247-25",
            "dependent_birthdate": "01/01/2000",
            "dependent_biological_sex": BiologicalSex.MALE,
            "dependent_email": "dependente.pp@example.com",
            "dependent_phone": "(11) 99999-0000",
            "dependent_password": "12345678",
            "dependent_password_confirm": "12345678",
            "dependent_kinship_type": "other",
            "dependent_kinship_other_label": "Familiar",
            "dependent_class_groups": [str(self.class_group.pk)],
            "dependent_blood_type": "",
            "dependent_allergies": "",
            "dependent_injuries": "",
            "dependent_emergency_contact": "Contato Emergencia",
            "dependent_has_martial_art": "yes",
            "dependent_martial_art": "jiu_jitsu",
            "dependent_martial_art_graduation": "",
            "dependent_jiu_jitsu_belt": "white",
            "dependent_jiu_jitsu_stripes": "0",
            "dependent_martial_art_started_at": "01/01/2024",
            "dependent_martial_art_last_graduation_at": "",
            "dependent_previous_academy": "Academia Exemplo",
            "use_family_plan": "",
            "selected_plan": "",
            "checkout_action": CheckoutAction.PAY_LATER,
            "materials_checkout_action": CheckoutAction.PAY_LATER,
        }
        payload.update(overrides)
        return payload

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.account.pk
        session.save()

    def test_dependent_selecting_plan_price_resolves_dependent_own(self):
        self._login()

        with patch(
            "system.services.dependent_registration.create_pre_registration_plan_payment"
        ) as mocked_payment:
            mocked_payment.return_value = "https://checkout.asaas.test/pp-session"
            response = self.client.post(
                reverse("system:dependent-add"),
                data=self._payload(
                    selected_plan=f"pp:{self.price.pk}",
                    checkout_action=CheckoutAction.PIX,
                ),
                follow=False,
            )

        self.assertEqual(response.status_code, 302)
        pre_registration = PreRegistration.objects.get()
        self.assertEqual(
            pre_registration.form_snapshot["financial_mode"],
            DependentFinancialMode.DEPENDENT_OWN,
        )
        self.assertIsNone(pre_registration.selected_plan)

    def test_dependent_own_plan_price_finalization_triggers_family_discount(self):
        pre_registration = PreRegistration.objects.create(
            registration_profile="dependent",
            holder_cpf=self.owner.cpf,
            holder_email=self.owner.email,
            form_snapshot={
                "flow_kind": "dependent_addition",
                "owner_person_id": self.owner.pk,
            },
        )
        cleaned_data = {
            "dependent_name": "Dependente Plan Price Final",
            "dependent_cpf": "153.509.460-56",
            "dependent_password": "12345678",
            "dependent_biological_sex": BiologicalSex.MALE,
            "financial_mode": DependentFinancialMode.DEPENDENT_OWN,
            "selected_plan_obj": self.price,
            "checkout_action": CheckoutAction.PIX,
        }

        result = finalize_dependent_registration(
            self.owner, cleaned_data, pre_registration=pre_registration
        )

        dependent = result["dependent"]
        dependent_membership = Membership.objects.get(person=dependent)
        self.assertEqual(dependent_membership.plan_price_id, self.price.pk)

        self.owner_membership.refresh_from_db()
        dependent_membership.refresh_from_db()
        self.assertTrue(self.owner_membership.family_discount_applied)
        self.assertTrue(dependent_membership.family_discount_applied)
        self.assertEqual(self.owner_membership.billed_price, self.price.family_price())
        self.assertEqual(dependent_membership.billed_price, self.price.family_price())
