from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models import CategoryAudience, ClassCategory, ClassGroup, ClassSchedule
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationClassesRoutesTestCase(TestCase):
    """PRD-077: rotas canonicas em ingles + CRUD curto em modal para Turmas/Categorias/Horarios."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-classes",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.category = ClassCategory.objects.create(
            code="adult-fundacao",
            display_name="Adulto Fundacao",
            audience=CategoryAudience.ADULT,
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Turma Fundacao",
            class_category=self.category,
        )
        self.schedule = ClassSchedule.objects.create(
            class_group=self.class_group,
            weekday="monday",
            training_style="mixed",
            start_time="19:00",
            duration_minutes=60,
        )
        self._login_technical_admin()

    def test_english_class_group_list_route_renders(self):
        response = self.client.get(reverse("system:class-group-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/classes/")

    def test_old_portuguese_class_group_list_redirects(self):
        response = self.client.get("/turmas/")
        self.assertRedirects(response, reverse("system:class-group-list"))

    def test_english_class_category_list_route_renders(self):
        response = self.client.get(reverse("system:class-category-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/classes/categories/")

    def test_english_class_schedule_list_route_renders(self):
        response = self.client.get(reverse("system:class-schedule-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/classes/schedules/")

    def test_class_group_detail_uses_real_pk_not_grouped_card(self):
        response = self.client.get(
            reverse("system:class-group-detail", kwargs={"pk": self.class_group.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["class_group"].pk, self.class_group.pk)

    def test_create_class_category_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:class-category-create") + "?modal=1",
            data={
                "code": "kids-fundacao",
                "display_name": "Kids Fundacao",
                "audience": CategoryAudience.KIDS,
                "description": "",
                "display_order": "0",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(ClassCategory.objects.filter(code="kids-fundacao").exists())

    def test_edit_class_group_modal_renders_modal_template_with_formset(self):
        response = self.client.get(
            reverse("system:class-group-update", kwargs={"pk": self.class_group.pk})
            + "?modal=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "classes/class_group_form.html")
        self.assertIn("schedule_formset", response.context)

    def test_create_class_schedule_modal_renders_modal_template(self):
        response = self.client.get(
            reverse("system:class-schedule-create") + "?modal=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "class_schedules/class_schedule_form.html")

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
