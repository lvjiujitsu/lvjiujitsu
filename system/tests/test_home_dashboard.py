from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import Person, PersonType, PortalAccount
from system.models.category import CategoryAudience
from system.models.graduation import BeltRank, Graduation
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY


class HomeDashboardContractTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-home",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )

    def test_technical_admin_home_renders_staff_sections(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Acesso rápido", content)
        self.assertIn("Pessoas", content)
        self.assertIn("Turmas", content)
        self.assertIn("Financeiro", content)
        self.assertIn("Graduação", content)
        self.assertIn("Materiais", content)
        self.assertIn("Planos", content)
        self.assertIn("Perfis e acessos", content)
        self.assertIn("Turmas de hoje", content)
        self.assertIn("Disponível", content)
        self.assertIn("A receber", content)
        self.assertIn("Pendências", content)
        self.assertIn(f'href="{reverse("system:person-list")}"', content)
        self.assertNotIn('href="/admin/"', content)
        self.assertNotIn("Django Admin", content)
        self.assertNotIn("quick-link--disabled", content)
        self.assertNotIn('href="#"', content)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()

    def test_administrative_student_home_shows_split_with_personal_graduation(self):
        admin_type = PersonType.objects.create(
            code="administrative-assistant",
            display_name="Administrativo",
        )
        belt = BeltRank.objects.create(
            code="adult-purple",
            display_name="Roxa",
            audience=CategoryAudience.ADULT,
            color_hex="#5b3a8c",
            tip_color_hex="#17171a",
            stripe_color_hex="#ececec",
        )
        person = Person.objects.create(
            full_name="Aline Blanch Freiria",
            cpf="920.000.011-81",
            person_type=admin_type,
            birth_date=date(2005, 7, 7),
            biological_sex="female",
            jiu_jitsu_belt="purple",
            jiu_jitsu_stripes=1,
        )
        Graduation.objects.create(
            person=person,
            belt_rank=belt,
            grade_number=1,
            awarded_at=date(2025, 12, 15),
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        self._login_portal_account(account)

        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="personal-area-title"', content)
        self.assertIn('id="staff-area-title"', content)
        self.assertIn("Minha área", content)
        self.assertIn("Gestão", content)
        self.assertIn("Minha faixa", content)
        self.assertIn("role-badge--primary", content)
        self.assertIn("Aluno", content)
        self.assertIn("Administrativo", content)

    def test_administrative_only_home_has_no_personal_area(self):
        admin_type = PersonType.objects.create(
            code="administrative-assistant",
            display_name="Administrativo",
        )
        person = Person.objects.create(
            full_name="Miguel Torres Dourado",
            cpf="920.000.012-62",
            person_type=admin_type,
            birth_date=date(1990, 3, 14),
            biological_sex="male",
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        self._login_portal_account(account)

        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="personal-area-title"', content)
        self.assertIn('id="staff-area-title"', content)
        self.assertIn("sem área pessoal de treino", content)
        self.assertIn("Acesso rápido", content)
        self.assertNotIn("Minha faixa", content)

    def _login_portal_account(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()
