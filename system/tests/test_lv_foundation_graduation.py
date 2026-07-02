from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Person, PersonType
from system.models.graduation import BeltRank, Graduation, GraduationRule
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationGraduationRoutesTestCase(TestCase):
    """PRD-077: rotas canonicas em ingles + CRUD curto em modal para Graduacao."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-graduation",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.belt_rank = BeltRank.objects.create(
            code="purple-fundacao",
            display_name="Roxa Fundacao",
            max_grades=4,
        )
        self.rule = GraduationRule.objects.create(
            belt_rank=self.belt_rank,
            from_grade=0,
            min_months_in_current_grade=12,
            min_classes_required=80,
            min_classes_window_months=12,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.student = Person.objects.create(
            full_name="Aluno Fundacao Graduacao",
            cpf="666.666.666-66",
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
        )
        self._login_technical_admin()

    def test_english_graduation_overview_route_renders(self):
        response = self.client.get(reverse("system:graduation-overview"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/graduation/")

    def test_old_portuguese_overview_redirects_to_english(self):
        response = self.client.get("/graduacao/")
        self.assertRedirects(response, reverse("system:graduation-overview"))

    def test_english_belt_rank_list_route_renders(self):
        response = self.client.get(reverse("system:belt-rank-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/graduation/belt-ranks/")

    def test_create_belt_rank_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:belt-rank-create") + "?modal=1",
            data={
                "code": "blue-fundacao",
                "display_name": "Azul Fundacao",
                "audience": "adult",
                "color_hex": "#0000ff",
                "tip_color_hex": "#000000",
                "stripe_color_hex": "#ffffff",
                "max_grades": "4",
                "display_order": "0",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(BeltRank.objects.filter(code="blue-fundacao").exists())

    def test_edit_graduation_rule_modal_renders_modal_template(self):
        response = self.client.get(
            reverse("system:graduation-rule-update", kwargs={"pk": self.rule.pk})
            + "?modal=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "graduation/graduation_rule_form.html")

    def test_create_graduation_modal_post_valid_renders_modal_done_and_preserves_history(self):
        response = self.client.post(
            reverse("system:graduation-create") + "?modal=1",
            data={
                "person": self.student.pk,
                "belt_rank": self.belt_rank.pk,
                "grade_number": "0",
                "awarded_at": "2026-01-10",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(
            Graduation.objects.filter(person=self.student, belt_rank=self.belt_rank).exists()
        )

    def test_graduation_history_has_no_update_route(self):
        with self.assertRaises(Exception):
            reverse("system:graduation-update", kwargs={"pk": 1})

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
