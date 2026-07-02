from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationCalendarRoutesTestCase(TestCase):
    """PRD-077: rota canonica em ingles para o cronograma (calendario unico)."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-calendar",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self._login_technical_admin()

    def test_english_calendar_route_renders(self):
        response = self.client.get(reverse("system:calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/calendar/")

    def test_old_portuguese_route_redirects_to_english(self):
        response = self.client.get("/cronograma/")
        self.assertRedirects(response, reverse("system:calendar"))

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()


class CalendarDeadCodeRemovedTestCase(TestCase):
    """PRD-097/PRD-077: views de calendario orfas (sem rota) foram removidas."""

    def test_admin_calendar_view_no_longer_exists(self):
        from system.views import calendar_views

        self.assertFalse(hasattr(calendar_views, "AdminCalendarView"))
        self.assertFalse(hasattr(calendar_views, "AdminToggleSessionView"))
        self.assertFalse(hasattr(calendar_views, "AdminSpecialClassCreateView"))
        self.assertFalse(hasattr(calendar_views, "AdminSpecialClassDeleteView"))
