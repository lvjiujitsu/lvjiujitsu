from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from system.constants import PersonTypeCode
from system.models import (
    BeltRank,
    BillingCycle,
    BiologicalSex,
    Graduation,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PlanAudience,
    PlanPaymentMethod,
    PortalAccount,
    SubscriptionPlan,
)
from system.models.category import CategoryAudience
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.services import PORTAL_ACCOUNT_SESSION_KEY


class HomeDependentsSectionTestCase(TestCase):

    def setUp(self):
        self.guardian_type = PersonType.objects.create(
            code=PersonTypeCode.GUARDIAN,
            display_name="Responsável",
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.guardian = Person.objects.create(
            full_name="Responsável Fundacao Dependentes",
            cpf="390.533.447-05",
            person_type=self.guardian_type,
            birth_date=date(1980, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Fundacao Dependentes",
            cpf="529.982.247-25",
            person_type=self.student_type,
            birth_date=date(2012, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        PersonRelationship.objects.create(
            source_person=self.guardian,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

    def test_guardian_home_shows_dependents_section(self):
        self._login_as(self.guardian)
        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Meus dependentes", content)
        self.assertIn("Dependente Fundacao Dependentes", content)

    def test_home_uses_client_profile_modal_instead_of_large_header(self):
        self._login_as(self.guardian)

        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('class="page-header"', content)
        self.assertIn('class="btn-icon js-open-client-profile"', content)
        self.assertIn('id="client-profile-modal"', content)
        self.assertIn("Dados do cliente", content)
        self.assertIn("Editar cadastro", content)
        self.assertIn("Excluir cadastro", content)

    def test_client_profile_update_changes_allowed_fields_and_preserves_cpf(self):
        self._login_as(self.guardian)

        response = self.client.post(
            reverse("system:client-profile-update"),
            data={
                "full_name": "Responsável Editado Conta",
                "cpf": "000.000.000-00",
                "birth_date": "1980-02-03",
                "biological_sex": BiologicalSex.MALE,
                "email": "conta.editada@example.com",
                "phone": "(11) 97777-1234",
                "postal_code": "01001-000",
                "address": "Rua Conta",
                "address_number": "123",
                "address_complement": "Sala 2",
                "address_neighborhood": "Centro",
                "city": "São Paulo",
                "blood_type": "",
                "allergies": "Sem alergias",
                "previous_injuries": "",
                "emergency_contact": "Contato Conta",
                "martial_art": "jiu_jitsu",
                "martial_art_graduation": "",
                "jiu_jitsu_belt": "blue",
                "jiu_jitsu_stripes": "1",
                "martial_art_started_at": "2022-01-01",
                "martial_art_last_graduation_at": "2024-01-01",
                "previous_academy": "Academia Conta",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.guardian.refresh_from_db()
        self.assertEqual(self.guardian.full_name, "Responsável Editado Conta")
        self.assertEqual(self.guardian.email, "conta.editada@example.com")
        self.assertEqual(self.guardian.cpf, "390.533.447-05")
        self.assertEqual(self.guardian.jiu_jitsu_belt, "blue")
        self.assertEqual(self.guardian.jiu_jitsu_stripes, 1)

    def test_client_profile_update_returns_field_errors(self):
        self._login_as(self.guardian)

        response = self.client.post(
            reverse("system:client-profile-update"),
            data={
                "full_name": "",
                "birth_date": "1980-02-03",
                "biological_sex": BiologicalSex.MALE,
                "email": "email-invalido",
                "phone": "(11) 97777-1234",
            },
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("full_name", data["errors"])
        self.assertIn("email", data["errors"])

    def test_client_profile_deactivate_disables_person_account_and_session(self):
        account = self._login_as(self.guardian)

        response = self.client.post(
            reverse("system:client-profile-deactivate"),
            data={"confirm": "ENCERRAR"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["redirect_url"], reverse("system:login"))
        self.guardian.refresh_from_db()
        account.refresh_from_db()
        self.assertFalse(self.guardian.is_active)
        self.assertFalse(account.is_active)
        self.assertNotIn(PORTAL_ACCOUNT_SESSION_KEY, self.client.session)

    def test_guardian_home_separates_owner_and_dependent_billing_and_crud(self):
        self.guardian.jiu_jitsu_belt = "blue"
        self.guardian.save(update_fields=["jiu_jitsu_belt", "updated_at"])
        owner_plan = self._create_plan("owner-prd121", "Plano Titular PRD 121")
        dependent_plan = self._create_plan("dependent-prd121", "Plano Dependente PRD 121")
        Membership.objects.create(
            person=self.guardian,
            plan=owner_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        Membership.objects.create(
            person=self.dependent,
            plan=dependent_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        belt = BeltRank.objects.create(
            code="adult-blue-prd121",
            display_name="Azul",
            audience=CategoryAudience.ADULT,
            color_hex="#1d4ed8",
            tip_color_hex="#111111",
            stripe_color_hex="#ffffff",
        )
        Graduation.objects.create(
            person=self.dependent,
            belt_rank=belt,
            grade_number=2,
            awarded_at=date(2024, 3, 15),
        )
        self._login_as(self.guardian)

        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Plano Titular PRD 121", content)
        self.assertIn("Mensalidade do dependente", content)
        self.assertIn("Plano Dependente PRD 121", content)
        self.assertIn("Remover dependente", content)
        self.assertIn(
            f'action="{reverse("system:dependent-profile-update", args=[self.dependent.pk])}"',
            content,
        )
        self.assertIn(
            f'action="{reverse("system:dependent-remove", args=[self.dependent.pk])}"',
            content,
        )

    def test_student_without_dependents_can_start_dependent_registration(self):
        self._login_as(self.dependent)
        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")
        modal_url = f"{reverse('system:dependent-add')}?modal=1"

        self.assertEqual(response.status_code, 200)
        self.assertIn("Dependentes", content)
        self.assertIn("Adicionar dependente", content)
        self.assertIn('id="dependent-registration-modal"', content)
        self.assertNotIn('class="section__link js-open-dependent-modal"', content)
        self.assertIn(
            'class="btn btn--secondary btn--sm section-action js-open-dependent-modal"',
            content,
        )
        self.assertIn('aria-label="Adicionar dependente"', content)
        self.assertIn('class="section-action__icon"', content)
        self.assertIn('class="section-action__text">Adicionar dependente</span>', content)
        self.assertIn(f'data-dependent-modal-url="{modal_url}"', content)
        self.assertIn(f'href="{modal_url}"', content)

    def test_home_query_marks_dependent_modal_to_open(self):
        self._login_as(self.dependent)

        response = self.client.get(reverse("system:home"), {"dependent_modal": "1"})
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="dependent-registration-modal"', content)
        self.assertIn('data-open-on-load="true"', content)

    def test_owned_dependent_edit_updates_allowed_profile_fields(self):
        self._login_as(self.guardian)

        response = self.client.post(
            reverse("system:dependent-profile-update", args=[self.dependent.pk]),
            data={
                "full_name": "Dependente Editado PRD 121",
                "birth_date": "2012-02-03",
                "biological_sex": BiologicalSex.FEMALE,
                "email": "dependente.editado@example.com",
                "phone": "(11) 90000-1212",
                "blood_type": "",
                "allergies": "Sem alergias",
                "previous_injuries": "",
                "emergency_contact": "Contato PRD 121",
                "martial_art": "jiu_jitsu",
                "martial_art_graduation": "",
                "jiu_jitsu_belt": "blue",
                "jiu_jitsu_stripes": "2",
                "martial_art_started_at": "2023-01-01",
                "martial_art_last_graduation_at": "2024-03-15",
                "previous_academy": "Academia anterior",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.dependent.refresh_from_db()
        self.assertEqual(self.dependent.full_name, "Dependente Editado PRD 121")
        self.assertEqual(self.dependent.email, "dependente.editado@example.com")
        self.assertEqual(self.dependent.jiu_jitsu_belt, "blue")
        self.assertEqual(self.dependent.jiu_jitsu_stripes, 2)

    def test_non_owner_cannot_edit_dependent(self):
        other = Person.objects.create(
            full_name="Responsável Sem Vínculo",
            cpf="268.866.230-15",
            person_type=self.guardian_type,
            birth_date=date(1981, 2, 2),
            biological_sex=BiologicalSex.MALE,
        )
        self._login_as(other)

        response = self.client.post(
            reverse("system:dependent-profile-update", args=[self.dependent.pk]),
            data={"full_name": "Tentativa Indevida"},
        )

        self.assertEqual(response.status_code, 404)

    def test_owned_dependent_remove_deletes_relationship_only(self):
        self._login_as(self.guardian)

        response = self.client.post(
            reverse("system:dependent-remove", args=[self.dependent.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("system:home"))
        self.assertFalse(
            PersonRelationship.objects.filter(
                source_person=self.guardian,
                target_person=self.dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )
        self.assertTrue(Person.objects.filter(pk=self.dependent.pk).exists())

    def _login_as(self, person):
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()
        return account

    def _create_plan(self, code, display_name):
        return SubscriptionPlan.objects.create(
            code=code,
            display_name=display_name,
            audience=PlanAudience.ADULT,
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            price="228.80",
        )
