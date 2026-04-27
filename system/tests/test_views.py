import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from system.models import (
    BiologicalSex,
    ClassCategory,
    ClassCheckin,
    ClassGroup,
    ClassSchedule,
    ClassSession,
    DepositStatus,
    Membership,
    MembershipStatus,
    PaymentProvider,
    Person,
    PersonRelationship,
    PersonType,
    PortalAccount,
    RegistrationOrder,
    SpecialClass,
    SpecialClassCheckin,
    SubscriptionPlan,
    TrialAccessGrant,
    WeekdayCode,
)
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.services.class_overview import build_class_group_filter_value
from system.services.registration import sync_person_class_enrollments
from system.services.seeding import seed_class_catalog, seed_products
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY


User = get_user_model()


class PortalViewTestCase(TestCase):
    def setUp(self):
        self.django_admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@admin.com",
            password="admin",
        )
        self.student_type = PersonType.objects.create(
            code="student",
            display_name="Aluno",
        )
        self.administrative_type = PersonType.objects.create(
            code="administrative-assistant",
            display_name="Auxiliar administrativo",
        )
        self.dependent_type = PersonType.objects.create(
            code="dependent",
            display_name="Dependente",
        )
        self.instructor_type = PersonType.objects.create(
            code="instructor",
            display_name="Professor",
        )

    def _create_portal_account(self, *, full_name, cpf, password, person_type):
        person = Person.objects.create(
            full_name=full_name,
            cpf=cpf,
            email=f"{cpf.replace('.', '').replace('-', '')}@example.com",
            person_type=person_type,
        )
        access_account = PortalAccount(person=person)
        access_account.set_password(password)
        access_account.save()
        return access_account

    def _login_portal_account(self, access_account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = access_account.pk
        session.save()

    def test_root_route_returns_approved_home_page(self):
        response = self.client.get(reverse("system:root"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Falar com a LV")
        self.assertContains(response, "Cadastro")

    def test_root_route_includes_lv_favicon_metadata(self):
        response = self.client.get(reverse("system:root"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'rel="icon"')
        self.assertContains(response, "system/img/favicon-lv.svg")
        self.assertContains(response, 'rel="apple-touch-icon"')

    def test_favicon_route_redirects_to_lv_asset(self):
        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{settings.STATIC_URL}system/img/favicon-lv.svg",
        )

    def test_login_route_returns_portal_login_page(self):
        response = self.client.get(reverse("system:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Use seu CPF e senha para acessar o portal.")
        self.assertContains(response, "Esqueci minha senha")
        self.assertContains(response, "Mostrar")
        self.assertContains(response, "Criar conta")
        self.assertContains(response, "Falar com a LV")

    def test_register_route_renders_class_group_selection_copy(self):
        response = self.client.get(reverse("system:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sexo biológico")
        self.assertContains(response, "Rascunho salvo")

    def test_register_route_exposes_binary_martial_art_question_choices(self):
        response = self.client.get(reverse("system:register"))

        self.assertEqual(response.status_code, 200)
        question_choices = response.context["form"].fields["holder_has_martial_art"].choices
        self.assertEqual(
            question_choices,
            [
                ("", "Selecione"),
                ("yes", "Sim"),
                ("no", "Não"),
            ],
        )
        modality_choices = response.context["form"].fields["holder_martial_art"].choices
        self.assertEqual(modality_choices[0], ("", "Selecione"))
        self.assertNotContains(response, "Não possui")

    def test_register_route_exposes_logical_class_choices_once(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:register"))

        self.assertEqual(response.status_code, 200)
        choices = [
            label
            for value, label in response.context["form"].fields["holder_class_groups"].choices
            if value
        ]
        self.assertEqual(
            sum(label.startswith("Adulto · Jiu Jitsu") for label in choices),
            1,
        )

    def test_register_route_exposes_compact_schedule_sections_for_wizard(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:register"))

        self.assertEqual(response.status_code, 200)
        catalog = json.loads(response.context["registration_catalog_json"])
        adult_option = next(
            item for item in catalog if item["category_audience"] == "adult"
        )

        self.assertIn("compact_schedule_sections", adult_option)
        monday_section = adult_option["compact_schedule_sections"][0]
        self.assertEqual(monday_section["weekday_label"], "Segunda-feira")
        self.assertIn(
            {
                "time_label": "06:30",
                "teacher_label": "Layon Quirino",
                "line_label": "06:30 - Layon Quirino",
            },
            monday_section["entries"],
        )

    def test_register_route_exposes_product_variants_in_material_catalog(self):
        seed_products()

        response = self.client.get(reverse("system:register"))

        self.assertEqual(response.status_code, 200)
        catalog = json.loads(response.context["product_catalog_json"])
        belt = next(item for item in catalog if item["sku"] == "belt-lv")

        self.assertIn("variants", belt)
        self.assertGreater(len(belt["variants"]), 0)
        self.assertEqual(belt["variants"][0]["product_id"], belt["id"])
        self.assertIn("label", belt["variants"][0])
        self.assertIn("snapshot_name", belt["variants"][0])

    def test_registration_step_validation_blocks_existing_cpf(self):
        Person.objects.create(
            full_name="Aluno Existente",
            cpf="123.456.789-03",
            person_type=self.student_type,
        )

        response = self.client.post(
            reverse("system:registration-step-validate"),
            {
                "step_key": "holder",
                "registration_profile": "holder",
                "holder_name": "Novo Aluno",
                "holder_cpf": "12345678903",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": "male",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["valid"])
        self.assertIn("holder_cpf", payload["errors"])
        self.assertEqual(payload["errors"]["holder_cpf"], "CPF já cadastrado no sistema.")

    def test_registration_step_validation_blocks_missing_jiu_jitsu_belt(self):
        response = self.client.post(
            reverse("system:registration-step-validate"),
            {
                "step_key": "holder_medical",
                "registration_profile": "holder",
                "holder_has_martial_art": "yes",
                "holder_martial_art": "jiu_jitsu",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["valid"])
        self.assertEqual(
            payload["errors"]["holder_jiu_jitsu_belt"],
            "Informe a faixa de Jiu Jitsu.",
        )

    def test_login_with_invalid_numeric_identifier_returns_form_error(self):
        response = self.client.post(
            reverse("system:login"),
            {"identifier": "123", "password": "x"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informe um CPF com 11 dígitos ou use seu acesso técnico.")

    def test_register_route_creates_local_account_and_not_django_user(self):
        response = self.client.post(
            reverse("system:register"),
            {
                "registration_profile": "holder",
                "holder_name": "Aluno Teste",
                "holder_cpf": "12345678903",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": "male",
                "holder_phone": "(62) 99999-1212",
                "holder_email": "aluno@example.com",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("system:login"))
        person = Person.objects.get(cpf="123.456.789-03")
        self.assertTrue(hasattr(person, "access_account"))
        self.assertEqual(person.person_type.code, "student")
        self.assertEqual(User.objects.count(), 1)
        self.assertContains(response, "Cadastro registrado com sucesso")

    def test_register_other_profile_creates_single_selected_person_type(self):
        response = self.client.post(
            reverse("system:register"),
            {
                "registration_profile": "other",
                "other_type_code": "instructor",
                "other_name": "Equipe Tecnica LV",
                "other_cpf": "12345678904",
                "other_birthdate": "02/04/1990",
                "other_phone": "(62) 98888-0000",
                "other_email": "equipe@example.com",
                "other_password": "123456",
                "other_password_confirm": "123456",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("system:login"))
        person = Person.objects.get(cpf="123.456.789-04")
        self.assertTrue(hasattr(person, "access_account"))
        self.assertEqual(person.person_type.code, "instructor")

    def test_registered_holder_can_log_in_with_local_account(self):
        self.client.post(
            reverse("system:register"),
            {
                "registration_profile": "holder",
                "holder_name": "Aluno Teste",
                "holder_cpf": "12345678903",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": "male",
                "holder_phone": "(62) 99999-1212",
                "holder_email": "aluno@example.com",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
            },
        )

        response = self.client.post(
            reverse("system:login"),
            {"identifier": "12345678903", "password": "123456"},
            follow=True,
        )

        self.assertRedirects(response, reverse("system:student-home"))

    def test_technical_admin_can_log_in_through_portal_and_access_admin_routes(self):
        response = self.client.post(
            reverse("system:login"),
            {"identifier": "admin", "password": "admin"},
            follow=True,
        )

        self.assertRedirects(response, reverse("system:admin-home"))
        self.assertContains(response, "Painel master")
        self.assertContains(response, "Superfície técnica")
        session = self.client.session
        self.assertIn(TECHNICAL_ADMIN_SESSION_KEY, session)

        person_response = self.client.get(reverse("system:person-list"))
        self.assertEqual(person_response.status_code, 200)
        self.assertContains(person_response, "Pessoas")

    def test_technical_admin_session_is_separate_from_django_admin_login(self):
        self.client.force_login(self.django_admin_user)

        response = self.client.get(reverse("system:person-list"))

        self.assertRedirects(
            response,
            f'{reverse("system:login")}?next={reverse("system:person-list")}',
        )

    def test_administrative_portal_account_can_access_person_crud(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-00",
            password="123456",
            person_type=self.administrative_type,
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(reverse("system:person-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pessoas")

    def test_administrative_portal_account_dashboard_exposes_shortcuts(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-00",
            password="123456",
            person_type=self.administrative_type,
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(reverse("system:administrative-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rotinas mais usadas")
        self.assertContains(response, "Tipos")

    def test_administrative_portal_account_can_open_person_edit_form(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-00",
            password="123456",
            person_type=self.administrative_type,
        )
        target_person = Person.objects.create(
            full_name="Pessoa Alvo",
            cpf="321.654.987-99",
            person_type=self.student_type,
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": target_person.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar pessoa")

    def test_person_list_keeps_summary_and_person_detail_shows_teacher_context(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-07",
            password="123456",
            person_type=self.administrative_type,
        )
        instructor = Person.objects.create(
            full_name="Professor Contexto",
            cpf="321.654.987-77",
            person_type=self.instructor_type,
        )
        adult_category = ClassCategory.objects.create(
            code="adult-test",
            display_name="Adulto",
            audience="adult",
        )
        class_group = ClassGroup.objects.create(
            code="adult-context",
            display_name="Jiu Jitsu",
            class_category=adult_category,
            main_teacher=instructor,
        )
        ClassSchedule.objects.create(
            class_group=class_group,
            weekday="monday",
            training_style="gi",
            start_time="07:00",
            duration_minutes=60,
            display_order=1,
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(reverse("system:person-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Professor Contexto")
        self.assertContains(response, "Visualizar")
        self.assertNotContains(response, "Segunda-feira · 07:00")

        detail_response = self.client.get(
            reverse("system:person-detail", kwargs={"pk": instructor.pk})
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Atuação como professor")
        self.assertContains(detail_response, "Adulto · Jiu Jitsu")
        self.assertContains(detail_response, "Segunda-feira")
        self.assertContains(detail_response, "07:00")

    def test_person_list_supports_operational_filters(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-10",
            password="123456",
            person_type=self.administrative_type,
        )
        adult_category = ClassCategory.objects.create(
            code="adult-filter",
            display_name="Adulto",
            audience="adult",
        )
        instructor = Person.objects.create(
            full_name="Lauro Filtro",
            cpf="321.654.987-81",
            person_type=self.instructor_type,
        )
        student = Person.objects.create(
            full_name="Aluno Filtro",
            cpf="321.654.987-82",
            person_type=self.student_type,
        )
        Person.objects.create(
            full_name="Outro Cadastro",
            cpf="321.654.987-83",
            person_type=self.student_type,
        )
        class_group = ClassGroup.objects.create(
            code="adult-filter-group",
            display_name="Jiu Jitsu",
            class_category=adult_category,
            main_teacher=instructor,
        )
        class_schedule = ClassSchedule.objects.create(
            class_group=class_group,
            weekday="monday",
            training_style="gi",
            start_time="19:00",
            duration_minutes=60,
            display_order=1,
        )
        student.class_category = adult_category
        student.class_group = class_group
        student.class_schedule = class_schedule
        student.save(update_fields=("class_category", "class_group", "class_schedule", "updated_at"))
        self._login_portal_account(administrative_account)

        teacher_response = self.client.get(
            reverse("system:person-list"),
            {
                "full_name": "Lauro",
                "cpf": "321.654.987-81",
                "is_teacher": "on",
                "class_category": adult_category.pk,
                "class_group_key": f"{adult_category.pk}::{class_group.display_name}",
                "weekday": "monday",
            },
        )

        self.assertEqual(teacher_response.status_code, 200)
        self.assertContains(teacher_response, "Lauro Filtro")
        self.assertNotContains(teacher_response, "Aluno Filtro")
        self.assertContains(teacher_response, "Somente professores")

        student_response = self.client.get(
            reverse("system:person-list"),
            {
                "full_name": "Aluno",
                "class_category": adult_category.pk,
                "class_group_key": f"{adult_category.pk}::{class_group.display_name}",
                "weekday": "monday",
            },
        )

        self.assertEqual(student_response.status_code, 200)
        self.assertContains(student_response, "Aluno Filtro")
        self.assertNotContains(student_response, "Outro Cadastro")

    def test_person_list_renders_filter_form_and_red_delete_action(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-11",
            password="123456",
            person_type=self.administrative_type,
        )
        Person.objects.create(
            full_name="Pessoa Excluir",
            cpf="321.654.987-84",
            person_type=self.student_type,
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(reverse("system:person-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Filtrar")
        self.assertContains(response, "Nome")
        self.assertContains(response, "CPF")
        self.assertContains(response, "Somente professores")
        self.assertContains(response, "danger-link")

    def test_person_detail_groups_student_classes_once_and_shows_student_schedules(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-12",
            password="123456",
            person_type=self.administrative_type,
        )
        seed_class_catalog()
        adult_category = ClassCategory.objects.get(code="adult")
        adult_groups = list(
            ClassGroup.objects.filter(
                class_category=adult_category,
                display_name="Jiu Jitsu",
            ).order_by("code")
        )
        student = Person.objects.create(
            full_name="Aluno Adulto Logico",
            cpf="321.654.987-85",
            birth_date=date(1994, 8, 12),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
            class_category=adult_category,
            class_group=adult_groups[0],
        )
        sync_person_class_enrollments(student, adult_groups)
        self._login_portal_account(administrative_account)

        response = self.client.get(
            reverse("system:person-detail", kwargs={"pk": student.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adulto · Jiu Jitsu")
        self.assertContains(response, "Horários liberados")
        self.assertContains(response, "Segunda-feira")
        self.assertContains(response, "06:30")
        self.assertContains(response, "11:00")
        self.assertContains(response, "19:00")
        content = response.content.decode("utf-8")
        self.assertTrue(content.index("06:30") < content.index("11:00") < content.index("19:00"))

    def test_person_detail_shows_responsible_billing_context_for_dependent(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao Financeiro",
            cpf="321.654.987-14",
            password="123456",
            person_type=self.administrative_type,
        )
        responsible = Person.objects.create(
            full_name="Responsável Financeiro",
            cpf="321.654.987-15",
            person_type=self.student_type,
        )
        dependent = Person.objects.create(
            full_name="Dependente Financeiro",
            cpf="321.654.987-16",
            person_type=self.dependent_type,
        )
        PersonRelationship.objects.create(
            source_person=responsible,
            target_person=dependent,
        )
        plan = SubscriptionPlan.objects.create(
            code="mensal-admin-responsavel",
            display_name="Plano Administrativo",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        Membership.objects.create(
            person=responsible,
            plan=plan,
            status=MembershipStatus.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(
            reverse("system:person-detail", kwargs={"pk": dependent.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Financeiro vinculado ao responsável")
        self.assertContains(response, "Plano Administrativo")

    def test_person_update_form_renders_birth_date_and_logical_class_choice_once(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-13",
            password="123456",
            person_type=self.administrative_type,
        )
        seed_class_catalog()
        adult_category = ClassCategory.objects.get(code="adult")
        adult_groups = list(
            ClassGroup.objects.filter(
                class_category=adult_category,
                display_name="Jiu Jitsu",
            ).order_by("code")
        )
        student = Person.objects.create(
            full_name="Aluno Editavel",
            cpf="321.654.987-86",
            birth_date=date(1994, 8, 12),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
            class_category=adult_category,
            class_group=adult_groups[0],
        )
        sync_person_class_enrollments(student, adult_groups)
        self._login_portal_account(administrative_account)

        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": student.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="1994-08-12"', html=False)
        self.assertContains(response, "Adulto · Jiu Jitsu", count=1)

    def test_person_type_detail_shows_people_of_that_type(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-08",
            password="123456",
            person_type=self.administrative_type,
        )
        teacher = Person.objects.create(
            full_name="Professor Tipo",
            cpf="321.654.987-78",
            person_type=self.instructor_type,
        )
        self._login_portal_account(administrative_account)

        response = self.client.get(
            reverse("system:person-type-detail", kwargs={"pk": self.instructor_type.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pessoas vinculadas")
        self.assertContains(response, teacher.full_name)

    def test_class_category_detail_shows_linked_groups_and_people(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao LV",
            cpf="321.654.987-09",
            password="123456",
            person_type=self.administrative_type,
        )
        instructor = Person.objects.create(
            full_name="Professor Categoria",
            cpf="321.654.987-79",
            person_type=self.instructor_type,
        )
        student = Person.objects.create(
            full_name="Aluno Categoria",
            cpf="321.654.987-80",
            person_type=self.student_type,
        )
        adult_category = ClassCategory.objects.create(
            code="adult-category-detail",
            display_name="Adulto",
            audience="adult",
        )
        ClassGroup.objects.create(
            code="adult-category-group",
            display_name="Jiu Jitsu",
            class_category=adult_category,
            main_teacher=instructor,
        )
        student.class_category = adult_category
        student.save(update_fields=("class_category", "updated_at"))
        self._login_portal_account(administrative_account)

        response = self.client.get(
            reverse("system:class-category-detail", kwargs={"pk": adult_category.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Turmas vinculadas")
        self.assertContains(response, "Pessoas nesta categoria")
        self.assertContains(response, instructor.full_name)
        self.assertContains(response, student.full_name)

    def test_anonymous_user_is_redirected_to_login_when_opening_person_edit_form(self):
        target_person = Person.objects.create(
            full_name="Pessoa Alvo",
            cpf="321.654.987-98",
            person_type=self.student_type,
        )

        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": target_person.pk})
        )

        self.assertRedirects(
            response,
            f'{reverse("system:login")}?next='
            f'{reverse("system:person-update", kwargs={"pk": target_person.pk})}',
        )

    def test_dependent_only_portal_account_can_access_student_home(self):
        self._create_portal_account(
            full_name="Dependente LV",
            cpf="321.654.987-02",
            password="123456",
            person_type=self.dependent_type,
        )

        response = self.client.post(
            reverse("system:login"),
            {"identifier": "32165498702", "password": "123456"},
            follow=True,
        )

        self.assertRedirects(response, reverse("system:student-home"))

    def test_instructor_portal_account_can_access_instructor_home(self):
        instructor_account = self._create_portal_account(
            full_name="Professor LV",
            cpf="321.654.987-03",
            password="123456",
            person_type=self.instructor_type,
        )

        response = self.client.post(
            reverse("system:login"),
            {"identifier": "32165498703", "password": "123456"},
            follow=True,
        )

        self.assertRedirects(response, reverse("system:instructor-home"))

    def test_instructor_dashboard_shows_today_classes_checkins_and_history(self):
        instructor_account = self._create_portal_account(
            full_name="Professor Dashboard",
            cpf="321.654.987-33",
            password="123456",
            person_type=self.instructor_type,
        )
        adult_category = ClassCategory.objects.create(
            code="adult-instructor-dashboard",
            display_name="Adulto",
            audience="adult",
        )
        class_group = ClassGroup.objects.create(
            code="adult-instructor-group",
            display_name="Turma Professor",
            class_category=adult_category,
            main_teacher=instructor_account.person,
        )
        weekday_map = {
            0: WeekdayCode.MONDAY,
            1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY,
            3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY,
            5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        schedule = ClassSchedule.objects.create(
            class_group=class_group,
            weekday=weekday_map[timezone.localdate().weekday()],
            training_style="gi",
            start_time="19:00",
            duration_minutes=60,
        )
        student_person = Person.objects.create(
            full_name="Aluno Presente",
            cpf="321.654.987-34",
            person_type=self.student_type,
            birth_date=date(2000, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        session = ClassSession.objects.create(
            schedule=schedule,
            date=timezone.localdate(),
        )
        ClassCheckin.objects.create(
            session=session,
            person=student_person,
        )
        special_class = SpecialClass.objects.create(
            title="Aulão do Professor",
            date=timezone.localdate(),
            start_time="20:00",
            duration_minutes=90,
            teacher=instructor_account.person,
        )
        SpecialClassCheckin.objects.create(
            special_class=special_class,
            person=student_person,
        )
        self._login_portal_account(instructor_account)

        response = self.client.get(reverse("system:instructor-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aulas do dia")
        self.assertContains(response, "Ver cronograma")
        self.assertContains(response, "Turma Professor")
        self.assertContains(response, "Aluno Presente")
        self.assertContains(response, "Histórico de check-ins")
        self.assertContains(response, "Aulão do Professor")

    def test_instructor_can_access_schedule_route(self):
        instructor_account = self._create_portal_account(
            full_name="Professor Agenda",
            cpf="321.654.987-35",
            password="123456",
            person_type=self.instructor_type,
        )
        self._login_portal_account(instructor_account)

        response = self.client.get(reverse("system:student-schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cronograma de Aulas")

    def test_student_dashboard_shows_checkin_attendance_history(self):
        student_account = self._create_portal_account(
            full_name="Aluno Histórico",
            cpf="321.654.987-36",
            password="123456",
            person_type=self.student_type,
        )
        instructor = Person.objects.create(
            full_name="Professor Histórico",
            cpf="321.654.987-37",
            person_type=self.instructor_type,
        )
        adult_category = ClassCategory.objects.create(
            code="adult-student-history",
            display_name="Adulto",
            audience="adult",
        )
        class_group = ClassGroup.objects.create(
            code="adult-student-history-group",
            display_name="Turma Histórico",
            class_category=adult_category,
            main_teacher=instructor,
        )
        weekday_map = {
            0: WeekdayCode.MONDAY,
            1: WeekdayCode.TUESDAY,
            2: WeekdayCode.WEDNESDAY,
            3: WeekdayCode.THURSDAY,
            4: WeekdayCode.FRIDAY,
            5: WeekdayCode.SATURDAY,
            6: WeekdayCode.SUNDAY,
        }
        schedule = ClassSchedule.objects.create(
            class_group=class_group,
            weekday=weekday_map[timezone.localdate().weekday()],
            training_style="gi",
            start_time="18:00",
            duration_minutes=60,
        )
        session = ClassSession.objects.create(
            schedule=schedule,
            date=timezone.localdate(),
        )
        ClassCheckin.objects.create(
            session=session,
            person=student_account.person,
        )
        self._login_portal_account(student_account)

        response = self.client.get(reverse("system:student-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Histórico de aulas com check-in confirmado")
        self.assertContains(response, "Turma Histórico")
        self.assertContains(response, "Professor Histórico")

    def test_portal_logout_clears_local_and_technical_sessions(self):
        student_account = self._create_portal_account(
            full_name="Aluno LV",
            cpf="321.654.987-01",
            password="123456",
            person_type=self.student_type,
        )
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = student_account.pk
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.django_admin_user.pk
        session.save()

        response = self.client.post(reverse("system:logout"), follow=True)

        self.assertRedirects(response, reverse("system:root"))
        session = self.client.session
        self.assertNotIn(PORTAL_ACCOUNT_SESSION_KEY, session)
        self.assertNotIn(TECHNICAL_ADMIN_SESSION_KEY, session)

    def test_chrome_devtools_probe_route_returns_no_content(self):
        response = self.client.get("/.well-known/appspecific/com.chrome.devtools.json")

        self.assertEqual(response.status_code, 204)

    def test_payment_checkout_with_missing_order_redirects_to_home_with_message(self):
        response = self.client.get(
            reverse("system:payment-checkout", kwargs={"order_id": 999999}),
            follow=True,
        )

        self.assertRedirects(response, reverse("system:root"))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Pedido não encontrado.", messages)

    def test_payment_checkout_without_authorization_redirects_to_home_with_message(self):
        plan = SubscriptionPlan.objects.create(
            code="mensal-pagamento",
            display_name="Mensal",
            price=Decimal("150.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        order_owner = Person.objects.create(
            full_name="Aluno Checkout",
            cpf="321.654.987-90",
            person_type=self.student_type,
        )
        order = RegistrationOrder.objects.create(
            person=order_owner,
            plan=plan,
            plan_price=Decimal("150.00"),
            total=Decimal("150.00"),
        )

        response = self.client.get(
            reverse("system:payment-checkout", kwargs={"order_id": order.pk}),
            follow=True,
        )

        self.assertRedirects(response, reverse("system:root"))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Pedido não encontrado.", messages)

    def test_payment_checkout_allows_dependent_when_order_belongs_to_responsible(self):
        plan = SubscriptionPlan.objects.create(
            code="mensal-relacao",
            display_name="Mensal Relação",
            price=Decimal("150.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        responsible_account = self._create_portal_account(
            full_name="Responsável Checkout",
            cpf="321.654.987-40",
            password="123456",
            person_type=self.student_type,
        )
        dependent_account = self._create_portal_account(
            full_name="Dependente Checkout",
            cpf="321.654.987-41",
            password="123456",
            person_type=self.dependent_type,
        )
        PersonRelationship.objects.create(
            source_person=responsible_account.person,
            target_person=dependent_account.person,
        )
        order = RegistrationOrder.objects.create(
            person=responsible_account.person,
            plan=plan,
            plan_price=Decimal("150.00"),
            total=Decimal("150.00"),
        )
        self._login_portal_account(dependent_account)

        response = self.client.get(
            reverse("system:payment-checkout", kwargs={"order_id": order.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pedido #")

    def test_financial_control_lists_gateway_fee_and_net_amount(self):
        administrative_account = self._create_portal_account(
            full_name="Recepcao Financeira",
            cpf="321.654.987-77",
            password="123456",
            person_type=self.administrative_type,
        )
        self._login_portal_account(administrative_account)
        plan = SubscriptionPlan.objects.create(
            code="standard-monthly-pix",
            display_name="Plano mensal PIX",
            price=Decimal("240.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
        )
        person = Person.objects.create(
            full_name="Aluno Entrada",
            cpf="321.654.987-78",
            person_type=self.student_type,
        )
        RegistrationOrder.objects.create(
            person=person,
            plan=plan,
            plan_price=Decimal("240.00"),
            total=Decimal("240.00"),
            payment_provider=PaymentProvider.ASAAS,
            administrative_fee=Decimal("1.99"),
            net_amount=Decimal("238.01"),
            deposit_status=DepositStatus.AVAILABLE,
            expected_deposit_date=date(2026, 4, 16),
        )

        response = self.client.get(reverse("system:financial-control"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Controle financeiro")
        self.assertContains(response, "Aluno Entrada")
        self.assertContains(response, "Plano mensal PIX")
        self.assertContains(response, "R$ 240,00")
        self.assertContains(response, "R$ 1,99")
        self.assertContains(response, "R$ 238,01")
        self.assertContains(response, "Disponível")

    def test_register_with_pay_later_grants_trial_and_redirects_to_login(self):
        plan = SubscriptionPlan.objects.create(
            code="mensal-trial",
            display_name="Mensal Trial",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        response = self.client.post(
            reverse("system:register"),
            {
                "registration_profile": "holder",
                "holder_name": "Aluno Trial",
                "holder_cpf": "12345678912",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": "male",
                "holder_phone": "(62) 99999-1212",
                "holder_email": "trial@example.com",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "selected_plan": str(plan.pk),
                "checkout_action": "pay_later",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("system:login"))
        order = RegistrationOrder.objects.get(person__cpf="123.456.789-12")
        grant = TrialAccessGrant.objects.get(order=order)
        self.assertEqual(grant.granted_classes, 1)
        self.assertEqual(grant.consumed_classes, 0)

    def test_register_with_card_action_redirects_directly_to_stripe_checkout(self):
        plan = SubscriptionPlan.objects.create(
            code="mensal-stripe",
            display_name="Mensal Stripe",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        response = self.client.post(
            reverse("system:register"),
            {
                "registration_profile": "holder",
                "holder_name": "Aluno Cartao",
                "holder_cpf": "12345678913",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": "male",
                "holder_phone": "(62) 99999-1313",
                "holder_email": "cartao@example.com",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "selected_plan": str(plan.pk),
                "checkout_action": "stripe",
            },
        )

        order = RegistrationOrder.objects.get(person__cpf="123.456.789-13")
        self.assertRedirects(
            response,
            reverse("system:stripe-checkout", kwargs={"order_id": order.pk}),
            fetch_redirect_response=False,
        )

    def test_pending_payment_with_trial_allows_login(self):
        plan = SubscriptionPlan.objects.create(
            code="mensal-login-trial",
            display_name="Mensal Login Trial",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        self.client.post(
            reverse("system:register"),
            {
                "registration_profile": "holder",
                "holder_name": "Aluno Login Trial",
                "holder_cpf": "12345678914",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": "male",
                "holder_phone": "(62) 99999-1414",
                "holder_email": "logintrial@example.com",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "selected_plan": str(plan.pk),
                "checkout_action": "pay_later",
            },
        )

        response = self.client.post(
            reverse("system:login"),
            {"identifier": "12345678914", "password": "123456"},
            follow=True,
        )

        self.assertRedirects(response, reverse("system:student-home"))
        self.assertContains(response, "período experimental")

    def test_student_dashboard_shows_active_membership_and_due_date(self):
        student_account = self._create_portal_account(
            full_name="Aluno Mensalidade",
            cpf="321.654.987-21",
            password="123456",
            person_type=self.student_type,
        )
        plan = SubscriptionPlan.objects.create(
            code="mensal-dashboard",
            display_name="Plano Mensal",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        Membership.objects.create(
            person=student_account.person,
            plan=plan,
            status=MembershipStatus.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self._login_portal_account(student_account)

        response = self.client.get(reverse("system:student-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano Mensal")
        self.assertContains(response, "Próximo vencimento")

    def test_student_dashboard_backfills_membership_from_paid_order(self):
        student_account = self._create_portal_account(
            full_name="Aluno Retroativo",
            cpf="321.654.987-22",
            password="123456",
            person_type=self.student_type,
        )
        plan = SubscriptionPlan.objects.create(
            code="mensal-retroativo",
            display_name="Plano Retroativo",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        RegistrationOrder.objects.create(
            person=student_account.person,
            plan=plan,
            plan_price=Decimal("250.00"),
            total=Decimal("250.00"),
            payment_status="paid",
            paid_at=timezone.now(),
        )
        self._login_portal_account(student_account)

        response = self.client.get(reverse("system:student-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano Retroativo")
        self.assertTrue(
            Membership.objects.filter(person=student_account.person, plan=plan).exists()
        )

    def test_student_dashboard_uses_responsible_membership_for_dependent(self):
        responsible_account = self._create_portal_account(
            full_name="Responsável Mensalidade",
            cpf="321.654.987-31",
            password="123456",
            person_type=self.student_type,
        )
        dependent_account = self._create_portal_account(
            full_name="Dependente Mensalidade",
            cpf="321.654.987-32",
            password="123456",
            person_type=self.dependent_type,
        )
        PersonRelationship.objects.create(
            source_person=responsible_account.person,
            target_person=dependent_account.person,
        )
        plan = SubscriptionPlan.objects.create(
            code="mensal-responsavel",
            display_name="Plano do Responsável",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        Membership.objects.create(
            person=responsible_account.person,
            plan=plan,
            status=MembershipStatus.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self._login_portal_account(dependent_account)

        response = self.client.get(reverse("system:student-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano do Responsável")
        self.assertContains(response, "vinculada ao responsável")

    @override_settings(STRIPE_SECRET_KEY="")
    @patch("system.views.payment_views.logger.error")
    def test_stripe_checkout_without_env_redirects_back_with_message(
        self, _mock_log_error
    ):
        plan = SubscriptionPlan.objects.create(
            code="mensal-env-stripe",
            display_name="Mensal Env Stripe",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        order_owner = Person.objects.create(
            full_name="Aluno Env Stripe",
            cpf="321.654.987-91",
            person_type=self.student_type,
        )
        order = RegistrationOrder.objects.create(
            person=order_owner,
            plan=plan,
            plan_price=Decimal("250.00"),
            total=Decimal("250.00"),
        )
        session = self.client.session
        session["pending_checkout_order_id"] = order.pk
        session.save()

        response = self.client.get(
            reverse("system:stripe-checkout", kwargs={"order_id": order.pk}),
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("system:payment-checkout", kwargs={"order_id": order.pk}),
        )
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("indisponível" in message for message in messages))

    @override_settings(ASAAS_API_KEY="")
    @patch("system.views.asaas_views.logger.error")
    def test_pix_checkout_without_env_redirects_back_with_message(
        self, _mock_log_error
    ):
        plan = SubscriptionPlan.objects.create(
            code="mensal-env-pix",
            display_name="Mensal Env PIX",
            price=Decimal("250.00"),
            billing_cycle="monthly",
            is_active=True,
        )
        order_owner = Person.objects.create(
            full_name="Aluno Env PIX",
            cpf="321.654.987-92",
            person_type=self.student_type,
        )
        order = RegistrationOrder.objects.create(
            person=order_owner,
            plan=plan,
            plan_price=Decimal("250.00"),
            total=Decimal("250.00"),
        )
        session = self.client.session
        session["pending_checkout_order_id"] = order.pk
        session.save()

        response = self.client.get(
            reverse("system:asaas-pix-create", kwargs={"order_id": order.pk}),
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("system:payment-checkout", kwargs={"order_id": order.pk}),
        )
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("PIX indisponível" in message for message in messages))


class PlanChangeSelectViewGroupingTest(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code="student",
            display_name="Aluno",
        )
        self.current_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-individual",
            display_name="Plano Mensal PIX",
            price=Decimal("240.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
            is_family_plan=False,
        )
        self.individual_plan = SubscriptionPlan.objects.create(
            code="mensal-credito-individual",
            display_name="Plano Mensal Crédito",
            price=Decimal("250.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.CREDIT_CARD,
            is_active=True,
            is_family_plan=False,
        )
        self.family_plan = SubscriptionPlan.objects.create(
            code="mensal-pix-familia",
            display_name="Plano Mensal PIX Família",
            price=Decimal("220.00"),
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            is_active=True,
            is_family_plan=True,
        )
        person = Person.objects.create(
            full_name="Aluno Teste",
            cpf="123.456.789-00",
            email="aluno@example.com",
            person_type=self.student_type,
        )
        self.membership = Membership.objects.create(
            person=person,
            plan=self.current_plan,
            status=MembershipStatus.ACTIVE,
            current_period_start=timezone.now() - timedelta(days=5),
            current_period_end=timezone.now() + timedelta(days=25),
        )
        self.portal_account = PortalAccount(person=person)
        self.portal_account.set_password("senha123")
        self.portal_account.save()

    def _login(self):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = self.portal_account.pk
        session.save()

    def test_plan_groups_context_contains_individual_and_family(self):
        self._login()
        response = self.client.get(reverse("system:plan-change-select"))

        self.assertEqual(response.status_code, 200)
        plan_groups = response.context["plan_groups"]
        labels = [g["label"] for g in plan_groups]
        self.assertIn("Planos Individuais", labels)
        self.assertIn("Planos Família", labels)

    def test_individual_group_excludes_family_plans(self):
        self._login()
        response = self.client.get(reverse("system:plan-change-select"))

        plan_groups = response.context["plan_groups"]
        individual_group = next(g for g in plan_groups if g["label"] == "Planos Individuais")
        family_flags = [e["plan"].is_family_plan for e in individual_group["entries"]]
        self.assertFalse(any(family_flags))

    def test_family_group_contains_only_family_plans(self):
        self._login()
        response = self.client.get(reverse("system:plan-change-select"))

        plan_groups = response.context["plan_groups"]
        family_group = next(g for g in plan_groups if g["label"] == "Planos Família")
        family_flags = [e["plan"].is_family_plan for e in family_group["entries"]]
        self.assertTrue(all(family_flags))

    def test_empty_group_is_omitted_from_plan_groups(self):
        self.family_plan.delete()
        self._login()
        response = self.client.get(reverse("system:plan-change-select"))

        plan_groups = response.context["plan_groups"]
        labels = [g["label"] for g in plan_groups]
        self.assertNotIn("Planos Família", labels)

    def test_template_renders_group_labels(self):
        self._login()
        response = self.client.get(reverse("system:plan-change-select"))

        self.assertContains(response, "Planos Individuais")
        self.assertContains(response, "Planos Família")

    def test_unauthenticated_access_redirected(self):
        response = self.client.get(reverse("system:plan-change-select"))
        self.assertNotEqual(response.status_code, 200)
