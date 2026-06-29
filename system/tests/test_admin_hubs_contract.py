from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from system.services import TECHNICAL_ADMIN_SESSION_KEY


class AdminHubRoutingContractTestCase(TestCase):
    admin_routes = (
        ("admin-hub", "/administracao/", {}),
        ("class-group-list", "/turmas/", {}),
        ("class-group-create", "/turmas/nova/", {}),
        ("class-group-detail", "/turmas/1/", {"pk": 1}),
        ("class-group-update", "/turmas/1/editar/", {"pk": 1}),
        ("class-group-delete", "/turmas/1/excluir/", {"pk": 1}),
        ("class-category-list", "/turmas/categorias/", {}),
        ("class-schedule-list", "/turmas/horarios/", {}),
        ("financial-control", "/financeiro/", {}),
        ("approval-queue", "/financeiro/aprovacoes/", {}),
        ("pending-payments", "/financeiro/pendentes/", {}),
        ("payroll-list", "/financeiro/folha/", {}),
        ("payout-queue", "/financeiro/repasses/", {}),
        ("graduation-overview", "/graduacao/", {}),
        ("belt-rank-list", "/graduacao/faixas/", {}),
        ("graduation-rule-list", "/graduacao/regras/", {}),
        ("graduation-list", "/graduacao/historico/", {}),
        ("product-list", "/materiais/", {}),
        ("product-create", "/materiais/novo/", {}),
        ("product-detail", "/materiais/1/", {"pk": 1}),
        ("admin-backorder-queue", "/materiais/pre-pedidos/", {}),
        ("product-store", "/loja/", {}),
        ("student-backorders", "/meus-materiais/pre-pedidos/", {}),
        ("student-order-history", "/meus-materiais/pedidos/", {}),
        ("person-type-list", "/administracao/perfis/", {}),
        ("person-type-create", "/administracao/perfis/novo/", {}),
        ("person-type-detail", "/administracao/perfis/1/", {"pk": 1}),
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
        self.assertIn('href="/admin/"', content)
        self.assertNotIn("Planos", content)
        self.assertNotIn("Turmas", content)
        self.assertNotIn("Financeiro", content)
        self.assertNotIn("Graduação", content)
        self.assertNotIn("Materiais", content)
        self.assertNotIn("Perfis e acessos", content)
        self.assertNotIn("quick-link--disabled", content)
        self.assertNotIn('href="#"', content)

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
