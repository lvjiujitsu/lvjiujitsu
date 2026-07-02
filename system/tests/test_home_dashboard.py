from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import OperationalRoleCode, PersonTypeCode, PortalCapability
from system.models import OperationalRole, Person, PersonOperationalRole, PersonType, PortalAccount
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
        self.assertIn("Tipos de vínculo", content)
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

    def test_class_assistant_student_home_has_no_administrative_area(self):
        student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        class_assistant_role = OperationalRole.objects.create(
            code=OperationalRoleCode.CLASS_ASSISTANT,
            display_name="Apoio de turma",
            capabilities=[PortalCapability.SUPPORT_CLASSES],
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
            person_type=student_type,
            birth_date=date(2005, 7, 7),
            biological_sex="female",
            jiu_jitsu_belt="purple",
            jiu_jitsu_stripes=1,
        )
        PersonOperationalRole.objects.create(
            person=person,
            role=class_assistant_role,
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
        self.assertIn("Apoio de turma", content)
        self.assertIn("Minha faixa", content)
        self.assertIn("role-badge--primary", content)
        self.assertIn("Aluno", content)
        self.assertNotIn("Administrativo", content)
        self.assertNotIn('id="quick-title"', content)
        self.assertNotIn('id="financial-title"', content)
        self.assertNotIn('id="staff-area-title"', content)
        self.assertIn(
            PortalCapability.SUPPORT_CLASSES,
            response.wsgi_request.portal_capabilities,
        )
        self.assertNotIn(
            PortalCapability.MANAGE_ACADEMY,
            response.wsgi_request.portal_capabilities,
        )

    def test_student_without_operational_role_has_no_administrative_area(self):
        student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        person = Person.objects.create(
            full_name="Miguel Torres Dourado",
            cpf="920.000.012-62",
            person_type=student_type,
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
        self.assertIn("Aluno", content)
        self.assertNotIn("Administrativo", content)
        self.assertNotIn('id="staff-area-title"', content)
        self.assertNotIn("sem área pessoal de treino", content)
        self.assertNotIn('id="quick-title"', content)
        self.assertNotIn("Minha faixa", content)

    def test_class_assistant_student_cannot_access_financial_control(self):
        student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        class_assistant_role = OperationalRole.objects.create(
            code=OperationalRoleCode.CLASS_ASSISTANT,
            display_name="Apoio de turma",
            capabilities=[PortalCapability.SUPPORT_CLASSES],
        )
        person = Person.objects.create(
            full_name="Aline Blanch Freiria",
            cpf="920.000.011-81",
            person_type=student_type,
            birth_date=date(2005, 7, 7),
            biological_sex="female",
            jiu_jitsu_belt="purple",
        )
        PersonOperationalRole.objects.create(
            person=person,
            role=class_assistant_role,
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        self._login_portal_account(account)

        response = self.client.get(reverse("system:financial-control"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("system:dashboard-redirect"))

    def test_dual_role_student_sees_own_checkin_merged_with_support_classes(self):
        from system.models import (
            ClassCategory,
            ClassEnrollment,
            ClassGroup,
            ClassSchedule,
            IbjjfAgeCategory,
        )
        from system.services.class_calendar import PYTHON_WEEKDAY_TO_CODE

        student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        class_assistant_role = OperationalRole.objects.create(
            code=OperationalRoleCode.CLASS_ASSISTANT,
            display_name="Apoio de turma",
            capabilities=[PortalCapability.SUPPORT_CLASSES],
        )
        category = ClassCategory.objects.create(
            code="adult-dual-role",
            display_name="Adulto Dual Role",
            audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult-dual-role",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            display_order=1,
        )
        class_group = ClassGroup.objects.create(
            display_name="Turma Dual Role",
            class_category=category,
        )
        today_weekday = PYTHON_WEEKDAY_TO_CODE[date.today().weekday()]
        ClassSchedule.objects.create(
            class_group=class_group,
            weekday=today_weekday,
            start_time="06:30",
        )
        person = Person.objects.create(
            full_name="Aline Blanch Freiria",
            cpf="920.000.011-81",
            person_type=student_type,
            birth_date=date(2005, 7, 7),
            biological_sex="female",
        )
        ClassEnrollment.objects.create(
            person=person,
            class_group=class_group,
            status="active",
        )
        PersonOperationalRole.objects.create(
            person=person,
            role=class_assistant_role,
        )
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        self._login_portal_account(account)

        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Turmas de hoje", content)
        self.assertIn("Check-in", content)
        self.assertNotIn('id="staff-area-title"', content)
        today_entries = response.context["today_classes"]
        self.assertTrue(
            any(getattr(entry, "entry_role", None) == "student" for entry in today_entries)
        )

    def _login_portal_account(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()
