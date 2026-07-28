from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.models.plan import SubscriptionPlan
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationPlansRoutesTestCase(TestCase):

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-plans",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.plan = SubscriptionPlan.objects.create(
            code="plan-fundacao",
            display_name="Plano Fundacao",
            audience="adult",
            weekly_frequency=2,
            billing_cycle="monthly",
            payment_method="pix",
            price="150.00",
        )
        self._login_technical_admin()

    def test_english_plan_list_route_renders(self):
        response = self.client.get(reverse("system:plan-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/plans/")

    def test_old_portuguese_list_route_redirects_to_english(self):
        response = self.client.get("/planos/")
        self.assertRedirects(response, reverse("system:plan-list"))

    def test_old_portuguese_edit_route_redirects_to_english(self):
        response = self.client.get(f"/planos/{self.plan.pk}/editar/")
        self.assertRedirects(
            response,
            reverse("system:plan-update", kwargs={"pk": self.plan.pk}),
        )

    def test_create_plan_modal_renders_modal_template(self):
        response = self.client.get(reverse("system:plan-create") + "?modal=1")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plans/plan_form_modal.html")
        self.assertNotContains(response, "<header class=\"topbar\"")

    def test_edit_plan_modal_renders_modal_template(self):
        response = self.client.get(
            reverse("system:plan-update", kwargs={"pk": self.plan.pk}) + "?modal=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plans/plan_form_modal.html")

    def test_create_plan_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:plan-create") + "?modal=1",
            data={
                "code": "plan-modal-novo",
                "display_name": "Plano Modal Novo",
                "audience": "adult",
                "weekly_frequency": "2",
                "billing_cycle": "monthly",
                "payment_method": "pix",
                "price": "199.90",
                "cycle_discount_percentage": "0",
                "teacher_commission_percentage": "0",
                "gateway_fixed_fee": "0",
                "gateway_percentage_fee": "0",
                "display_order": "0",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(SubscriptionPlan.objects.filter(code="plan-modal-novo").exists())

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
