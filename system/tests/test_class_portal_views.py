from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import (
    ClassCategory,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    PersonType,
)
from system.services.seeding import seed_class_catalog, seed_person_types


User = get_user_model()


class ClassPortalViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@admin.com",
            password="admin",
        )

    def _login_as_technical_admin(self):
        response = self.client.post(
            reverse("system:login"),
            {"identifier": "admin", "password": "admin"},
            follow=True,
        )
        self.assertRedirects(response, reverse("system:admin-home"))

    def _create_instructor(self, *, full_name, cpf):
        seed_person_types()
        instructor_type = PersonType.objects.get(code="instructor")
        return Person.objects.create(
            full_name=full_name,
            cpf=cpf,
            person_type=instructor_type,
        )

    def test_admin_home_exposes_class_crud_shortcuts(self):
        self._login_as_technical_admin()

        response = self.client.get(reverse("system:admin-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Turmas")
        self.assertContains(response, "Horários")
        self.assertContains(response, "Categorias")
        self.assertContains(response, "O que fazer agora")

    def test_technical_admin_can_access_class_crud_routes(self):
        seed_class_catalog()
        self._login_as_technical_admin()

        class_group_list_response = self.client.get(reverse("system:class-group-list"))
        class_schedule_list_response = self.client.get(reverse("system:class-schedule-list"))
        class_category_list_response = self.client.get(reverse("system:class-category-list"))

        self.assertEqual(class_group_list_response.status_code, 200)
        self.assertEqual(class_schedule_list_response.status_code, 200)
        self.assertEqual(class_category_list_response.status_code, 200)
        self.assertContains(class_group_list_response, "Turmas")
        self.assertContains(class_schedule_list_response, "Horários")
        self.assertContains(class_category_list_response, "Categorias")
        self.assertNotContains(class_group_list_response, "Público")
        self.assertNotContains(class_group_list_response, "Pública")

    def test_technical_admin_can_create_class_group_with_inline_schedule_and_assistant_team(self):
        self._login_as_technical_admin()
        adult_category = ClassCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience="adult",
        )
        main_teacher = self._create_instructor(
            full_name="Professor Principal",
            cpf="100.000.000-10",
        )
        assistant_teacher = self._create_instructor(
            full_name="Professor Auxiliar",
            cpf="100.000.000-11",
        )

        response = self.client.post(
            reverse("system:class-group-create"),
            {
                "code": "audit-test-class",
                "display_name": "Jiu Jitsu",
                "class_category": adult_category.pk,
                "main_teacher": main_teacher.pk,
                "description": "Turma criada durante teste de CRUD.",
                "default_capacity": 30,
                "assistant_staff": [assistant_teacher.pk],
                "is_active": "on",
                "schedules-TOTAL_FORMS": "1",
                "schedules-INITIAL_FORMS": "0",
                "schedules-MIN_NUM_FORMS": "0",
                "schedules-MAX_NUM_FORMS": "1000",
                "schedules-0-weekday": "monday",
                "schedules-0-training_style": "gi",
                "schedules-0-start_time": "07:00",
                "schedules-0-duration_minutes": "75",
                "schedules-0-display_order": "1",
                "schedules-0-is_active": "on",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("system:class-group-list"))
        class_group = ClassGroup.objects.get(code="audit-test-class")
        self.assertEqual(class_group.display_name, "Jiu Jitsu")
        self.assertEqual(class_group.main_teacher, main_teacher)
        self.assertTrue(
            ClassInstructorAssignment.objects.filter(
                class_group=class_group,
                person=assistant_teacher,
            ).exists()
        )
        self.assertTrue(
            ClassSchedule.objects.filter(
                class_group=class_group,
                weekday="monday",
                start_time="07:00",
            ).exists()
        )

    def test_active_class_group_without_inline_schedule_is_rejected(self):
        self._login_as_technical_admin()
        adult_category = ClassCategory.objects.create(
            code="adult-no-schedule",
            display_name="Adulto sem horário",
            audience="adult",
        )
        main_teacher = self._create_instructor(
            full_name="Professor Sem Horário",
            cpf="100.000.000-12",
        )

        response = self.client.post(
            reverse("system:class-group-create"),
            {
                "code": "adult-without-schedule",
                "display_name": "Jiu Jitsu",
                "class_category": adult_category.pk,
                "main_teacher": main_teacher.pk,
                "description": "Turma ativa sem horário.",
                "default_capacity": 20,
                "is_active": "on",
                "schedules-TOTAL_FORMS": "0",
                "schedules-INITIAL_FORMS": "0",
                "schedules-MIN_NUM_FORMS": "0",
                "schedules-MAX_NUM_FORMS": "1000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cadastre ao menos um horário ativo para a turma ativa.")
        self.assertFalse(ClassGroup.objects.filter(code="adult-without-schedule").exists())

    def test_public_info_page_reads_catalog_dynamically(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:info"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Turmas ativas")
        self.assertContains(response, "Adulto")
        self.assertContains(response, "Jiu Jitsu - Adulto")
        self.assertContains(response, "13 horários")
        self.assertContains(response, "3 professores")

    def test_public_info_page_exposes_dropdown_with_schedule_and_teaching_team(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:info"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ver horários e professores")
        self.assertContains(response, "Equipe docente")
        self.assertContains(response, "Segunda-feira")
        self.assertContains(response, "06:30")
        self.assertContains(response, "Professor principal")
        self.assertContains(response, "Jiu Jitsu - Adulto")

    def test_class_group_list_groups_logical_classes_once(self):
        seed_class_catalog()
        self._login_as_technical_admin()

        response = self.client.get(reverse("system:class-group-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adulto · Jiu Jitsu", count=1)
        self.assertContains(response, "3 professores")
        self.assertContains(response, "13 horários")
        self.assertNotContains(response, "Excluir")
        self.assertNotContains(response, "Editar")

    def test_class_group_detail_exposes_full_relations(self):
        seed_class_catalog()
        self._login_as_technical_admin()
        class_group = ClassGroup.objects.get(code="adult-layon")

        response = self.client.get(
            reverse("system:class-group-detail", kwargs={"pk": class_group.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipe docente")
        self.assertContains(response, "Layon Quirino")
        self.assertContains(response, "Vinicius Antonio")
        self.assertContains(response, "Lauro Viana")
        self.assertContains(response, "Segunda-feira")
        self.assertContains(response, "06:30")
        self.assertContains(response, "11:00")
        self.assertContains(response, "19:00")
        self.assertContains(response, "Editar")
        self.assertContains(response, "Excluir")

    def test_class_schedule_list_groups_by_weekday(self):
        seed_class_catalog()
        self._login_as_technical_admin()

        response = self.client.get(reverse("system:class-schedule-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Segunda-feira", count=1)
        self.assertContains(response, "4 horários")
        self.assertContains(response, "2 turmas")
        self.assertNotContains(response, "Excluir")
        self.assertNotContains(response, "Editar")

    def test_class_schedule_detail_exposes_full_relations(self):
        seed_class_catalog()
        self._login_as_technical_admin()
        class_schedule = ClassSchedule.objects.filter(
            class_group__code="adult-layon",
            weekday="monday",
        ).get()

        response = self.client.get(
            reverse("system:class-schedule-detail", kwargs={"pk": class_schedule.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ocorrências do dia")
        self.assertContains(response, "Adulto · Jiu Jitsu")
        self.assertContains(response, "Juvenil · Jiu Jitsu")
        self.assertContains(response, "Layon Quirino")
        self.assertContains(response, "Lauro Viana")
        self.assertContains(response, "Vinicius Antonio")
        self.assertContains(response, "06:30")
        self.assertContains(response, "11:00")
        self.assertContains(response, "18:00")
        self.assertContains(response, "19:00")

    def test_class_group_form_shows_existing_schedule_summary_grouped_by_weekday(self):
        self._login_as_technical_admin()
        adult_category = ClassCategory.objects.create(
            code="adult-summary",
            display_name="Adulto resumo",
            audience="adult",
        )
        main_teacher = self._create_instructor(
            full_name="Professor Resumo",
            cpf="100.000.000-13",
        )
        class_group = ClassGroup.objects.create(
            code="adult-summary-class",
            display_name="Jiu Jitsu",
            class_category=adult_category,
            main_teacher=main_teacher,
            is_active=True,
        )
        ClassSchedule.objects.create(
            class_group=class_group,
            weekday="monday",
            training_style="gi",
            start_time="06:30",
            duration_minutes=60,
            is_active=True,
        )
        ClassSchedule.objects.create(
            class_group=class_group,
            weekday="monday",
            training_style="no_gi",
            start_time="19:00",
            duration_minutes=60,
            is_active=True,
        )
        ClassSchedule.objects.create(
            class_group=class_group,
            weekday="wednesday",
            training_style="gi",
            start_time="07:00",
            duration_minutes=60,
            is_active=True,
        )

        response = self.client.get(
            reverse("system:class-group-update", kwargs={"pk": class_group.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumo atual")
        self.assertContains(response, "Segunda-feira · 06:30, 19:00")
        self.assertContains(response, "Quarta-feira · 07:00")
