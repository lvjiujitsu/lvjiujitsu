import re
from pathlib import Path

from django.test import SimpleTestCase
from django.urls import reverse


class PortugueseRedirectRoutesTestCase(SimpleTestCase):
    MIN_PT_REDIRECTS = 61

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        urls_path = Path(__file__).resolve().parents[1] / "urls.py"
        cls.redirect_count = len(re.findall(r"RedirectView\.as_view", urls_path.read_text(encoding="utf-8")))

    def test_pt_redirect_inventory_meets_prd_target(self):
        self.assertGreaterEqual(self.redirect_count, self.MIN_PT_REDIRECTS)

    def test_sample_pt_routes_redirect_to_canonical_names(self):
        samples = [
            ("/pessoas/", "system:person-list"),
            ("/planos/", "system:plan-list"),
            ("/turmas/", "system:class-group-list"),
            ("/financeiro/", "system:financial-control"),
            ("/graduacao/", "system:graduation-overview"),
            ("/materiais/", "system:product-list"),
            ("/cronograma/", "system:calendar"),
        ]
        for pt_path, name in samples:
            with self.subTest(pt_path=pt_path):
                response = self.client.get(pt_path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse(name))
