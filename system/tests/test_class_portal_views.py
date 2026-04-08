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
        self.assertContains(response, "Categorias")
        self.assertContains(response, "Professores")
        self.assertContains(response, "Horários")
        self.assertContains(response, "Turma")
        self.assertContains(response, "Adulto")
        self.assertContains(response, "Layon Quirino")
        self.assertContains(response, "Segunda-feira")

    def test_public_info_page_exposes_relational_team_and_schedule_sections(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:info"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipe docente")
        self.assertContains(response, "Ver por professor")
        self.assertContains(response, "Ver por horário")
        self.assertContains(response, "Feminino")
        self.assertContains(response, "Vannessa Ferro")
        self.assertNotContains(response, "Kimono")
