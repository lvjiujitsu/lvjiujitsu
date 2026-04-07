from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import ClassCategory, ClassGroup, ClassSchedule
from system.services.seeding import seed_class_catalog


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

    def test_technical_admin_can_create_class_group_and_schedule(self):
        self._login_as_technical_admin()
        adult_category = ClassCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience="adult",
        )

        class_group_response = self.client.post(
            reverse("system:class-group-create"),
            {
                "code": "audit-test-class",
                "display_name": "Jiu Jitsu",
                "class_category": adult_category.pk,
                "description": "Turma criada durante teste de CRUD.",
                "default_capacity": 30,
                "is_active": "on",
            },
            follow=True,
        )

        self.assertRedirects(class_group_response, reverse("system:class-group-list"))
        class_group = ClassGroup.objects.get(code="audit-test-class")
        self.assertEqual(class_group.display_name, "Jiu Jitsu")

        class_schedule_response = self.client.post(
            reverse("system:class-schedule-create"),
            {
                "class_group": class_group.pk,
                "weekday": "monday",
                "training_style": "gi",
                "start_time": "07:00",
                "duration_minutes": 75,
                "display_order": 1,
                "is_active": "on",
            },
            follow=True,
        )

        self.assertRedirects(class_schedule_response, reverse("system:class-schedule-list"))
        self.assertTrue(ClassSchedule.objects.filter(class_group=class_group, start_time="07:00").exists())

    def test_public_info_page_reads_catalog_dynamically(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:info"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Turmas, horários e professores.")
        self.assertContains(response, "Turma")
        self.assertContains(response, "Adulto")
        self.assertContains(response, "Layon Quirino")
        self.assertContains(response, "Segunda-feira")

    def test_public_info_page_exposes_only_summary_fields_and_primary_instructor(self):
        seed_class_catalog()

        response = self.client.get(reverse("system:info"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Turma")
        self.assertContains(response, "Professor")
        self.assertContains(response, "Horários")
        self.assertContains(response, "Feminino")
        self.assertContains(response, "Vannessa Ferro")
        self.assertNotContains(response, "Kimono")
        self.assertNotContains(response, "Resumo público")
        self.assertNotContains(response, "Nenhuma turma pública")
