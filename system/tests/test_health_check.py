
from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_responds_200_for_anonymous_user(self):
        response = self.client.get(reverse("system:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_is_reachable_by_path(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)

    def test_health_does_not_query_the_database(self):
        with self.assertNumQueries(0):
            self.client.get("/health/")
