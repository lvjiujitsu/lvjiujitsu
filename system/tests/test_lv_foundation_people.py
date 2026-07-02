from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Person, PersonType
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class LvFoundationPeopleRoutesTestCase(TestCase):
    """PRD-075: rotas canonicas em ingles + CRUD curto em modal para Pessoas."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-foundation",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.person = Person.objects.create(
            full_name="Pessoa Fundacao",
            cpf="444.444.444-44",
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
        )
        self._login_technical_admin()

    def test_english_person_list_route_renders(self):
        response = self.client.get(reverse("system:person-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/people/")

    def test_old_portuguese_list_route_redirects_to_english(self):
        response = self.client.get("/pessoas/")
        self.assertRedirects(response, reverse("system:person-list"))

    def test_old_portuguese_create_route_redirects_to_english(self):
        response = self.client.get("/pessoas/nova/")
        self.assertRedirects(response, reverse("system:person-create"))

    def test_old_portuguese_edit_route_redirects_to_english(self):
        response = self.client.get(f"/pessoas/{self.person.pk}/editar/")
        self.assertRedirects(
            response,
            reverse("system:person-update", kwargs={"pk": self.person.pk}),
        )

    def test_create_person_modal_renders_modal_template(self):
        response = self.client.get(reverse("system:person-create") + "?modal=1")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "people/person_form_modal.html")
        self.assertNotContains(response, "<header class=\"topbar\"")

    def test_edit_person_modal_renders_modal_template(self):
        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": self.person.pk}) + "?modal=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "people/person_form_modal.html")

    def test_view_person_modal_renders_modal_template(self):
        response = self.client.get(
            reverse("system:person-detail", kwargs={"pk": self.person.pk}) + "?modal=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "people/person_detail_modal.html")

    def test_create_person_modal_post_valid_renders_modal_done(self):
        response = self.client.post(
            reverse("system:person-create") + "?modal=1",
            data={
                "full_name": "Nova Pessoa Modal",
                "cpf": "529.982.247-25",
                "birth_date": "1995-05-05",
                "biological_sex": BiologicalSex.FEMALE.value,
                "person_type": self.student_type.pk,
                "has_martial_art": "no",
                "is_active": "on",
                "payroll_payment_day": "28",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lv/modal_done.html")
        self.assertTrue(Person.objects.filter(cpf="529.982.247-25").exists())

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
