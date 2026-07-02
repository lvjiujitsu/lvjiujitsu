from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from system.services import TECHNICAL_ADMIN_SESSION_KEY


class AdminHubRoutingContractTestCase(TestCase):
    admin_routes = (
        ("admin-hub", "/administration/", {}),
        ("class-group-list", "/classes/", {}),
        ("class-group-create", "/classes/create/", {}),
        ("class-group-detail", "/classes/1/view/", {"pk": 1}),
        ("class-group-update", "/classes/1/edit/", {"pk": 1}),
        ("class-group-delete", "/classes/1/delete/", {"pk": 1}),
        ("class-category-list", "/classes/categories/", {}),
        ("class-schedule-list", "/classes/schedules/", {}),
        ("financial-control", "/financial/", {}),
        ("approval-queue", "/financial/approvals/", {}),
        ("pending-payments", "/financial/pending/", {}),
        ("payroll-list", "/financial/payroll/", {}),
        ("payout-queue", "/financial/payouts/", {}),
        ("graduation-overview", "/graduation/", {}),
        ("belt-rank-list", "/graduation/belt-ranks/", {}),
        ("graduation-rule-list", "/graduation/rules/", {}),
        ("graduation-list", "/graduation/history/", {}),
        ("product-list", "/materials/", {}),
        ("product-create", "/materials/create/", {}),
        ("product-detail", "/materials/1/view/", {"pk": 1}),
        ("admin-backorder-queue", "/materials/backorders/", {}),
        ("product-store", "/store/", {}),
        ("student-backorders", "/my-materials/backorders/", {}),
        ("student-order-history", "/my-materials/orders/", {}),
        ("person-type-list", "/administration/person-types/", {}),
        ("person-type-create", "/administration/person-types/create/", {}),
        ("person-type-detail", "/administration/person-types/1/view/", {"pk": 1}),
    )

    def test_prd_065_named_routes_resolve_to_module_paths(self):
        missing_routes = []
        mismatched_routes = []

        for route_name, expected_path, kwargs in self.admin_routes:
            try:
                actual_path = reverse(f"system:{route_name}", kwargs=kwargs)
            except NoReverseMatch:
                missing_routes.append(route_name)
                continue

            if actual_path != expected_path:
                mismatched_routes.append(
                    f"{route_name}: expected {expected_path}, got {actual_path}"
                )

        self.assertEqual(
            missing_routes,
            [],
            "Rotas administrativas da PRD-065 ainda ausentes.",
        )
        self.assertEqual(
            mismatched_routes,
            [],
            "Rotas administrativas da PRD-065 resolveram para caminhos inesperados.",
        )


class AdminHomeHubContractTestCase(TestCase):
    expected_quick_links = (
        ("Pessoas", "system:person-list"),
        ("Turmas", "system:class-group-list"),
        ("Financeiro", "system:financial-control"),
        ("Graduação", "system:graduation-overview"),
        ("Materiais", "system:product-list"),
        ("Planos", "system:plan-list"),
        ("Tipos de vínculo", "system:person-type-list"),
    )

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-hubs",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )

    def test_technical_admin_home_links_to_enabled_admin_hubs(self):
        self._login_technical_admin()

        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Acesso rápido", content)
        for label, route_name in self.expected_quick_links:
            self.assertIn(label, content)
            self.assertIn(f'href="{reverse(route_name)}"', content)
        self.assertNotIn('href="/admin/"', content)
        self.assertNotIn("Django Admin", content)
        self.assertNotIn("quick-link--disabled", content)
        self.assertNotIn('href="#"', content)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
