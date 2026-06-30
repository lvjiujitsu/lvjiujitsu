from django.conf import settings
from django.test import Client, SimpleTestCase


class AllowedHostsSettingsTests(SimpleTestCase):
    def test_local_settings_do_not_allow_wildcard_hosts(self):
        self.assertIn("localhost", settings.ALLOWED_HOSTS)
        self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)
        self.assertNotIn("*", settings.ALLOWED_HOSTS)
        self.assertNotIn(".localhost", settings.ALLOWED_HOSTS)
        self.assertNotIn("lv.localhost", settings.ALLOWED_HOSTS)

    def test_lv_localhost_is_rejected(self):
        response = Client().get("/", HTTP_HOST="lv.localhost")

        self.assertEqual(response.status_code, 400)
