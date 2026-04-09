from datetime import date

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from system.models import (
    BiologicalSex,
    ClassCategory,
    ClassGroup,
    ClassSchedule,
    Person,
    PersonType,
    PortalAccount,
)
from system.services.class_overview import build_class_group_filter_value
from system.services.registration import sync_person_class_enrollments
from system.services.seeding import seed_class_catalog
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

    def test_legacy_login_form_route_returns_portal_login_page(self):
        response = self.client.get(reverse("system:legacy-login-form"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre com seu CPF e senha.")
        self.assertContains(response, "Esqueci minha senha")
        self.assertContains(response, "Mostrar")

    def test_register_route_renders_class_group_selection_copy(self):
        response = self.client.get(reverse("system:legacy-register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sexo biológico")
        self.assertContains(response, "Rascunho salvo")

    def test_register_route_exposes_logical_class_choices_once(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:legacy-register"))

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

    def test_login_with_invalid_numeric_identifier_returns_form_error(self):
        response = self.client.post(
            reverse("system:legacy-login-form"),
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

        self.assertRedirects(response, reverse("system:legacy-login-form"))
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

        self.assertRedirects(response, reverse("system:legacy-login-form"))
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
