from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    CategoryAudience,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    IbjjfAgeCategory,
    Person,
    PersonType,
    PortalAccount,
)
from system.services import PORTAL_ACCOUNT_SESSION_KEY, TECHNICAL_ADMIN_SESSION_KEY


class GuardianCanTrainTestCase(TestCase):
    """PRD-093: responsavel (guardian) pode receber turmas e treinar sem virar 'student'."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-guardian",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.guardian_type = PersonType.objects.create(
            code=PersonTypeCode.GUARDIAN,
            display_name="Responsável",
        )
        self.category = ClassCategory.objects.create(
            code="adult-guardian-fundacao",
            display_name="Adulto Guardian Fundacao",
            audience=CategoryAudience.ADULT,
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Turma Guardian Fundacao",
            class_category=self.category,
        )
        IbjjfAgeCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            display_order=1,
        )
        self.guardian = Person.objects.create(
            full_name="Responsável Fundacao",
            cpf="390.533.447-05",
            person_type=self.guardian_type,
            birth_date=date(1980, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        self._login_technical_admin()

    def test_guardian_can_receive_class_groups_on_update(self):
        response = self.client.post(
            reverse("system:person-update", kwargs={"pk": self.guardian.pk}),
            data={
                "full_name": "Responsável Fundacao",
                "cpf": "390.533.447-05",
                "birth_date": "1980-01-01",
                "biological_sex": BiologicalSex.FEMALE.value,
                "person_type": self.guardian_type.pk,
                "has_martial_art": "no",
                "is_active": "on",
                "payroll_payment_day": "28",
                "class_groups": [
                    f"{self.category.pk}::{self.class_group.display_name}"
                ],
            },
        )
        self.assertEqual(response.status_code, 302, response.context["form"].errors if response.status_code == 200 else "")
        self.assertTrue(
            ClassEnrollment.objects.filter(
                person=self.guardian, class_group=self.class_group, status="active"
            ).exists()
        )

    def test_guardian_with_enrollment_has_personal_home_area(self):
        ClassEnrollment.objects.create(
            person=self.guardian,
            class_group=self.class_group,
            status="active",
        )
        account = PortalAccount(person=self.guardian)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Responsável", content)
        self.assertTrue(response.context["has_personal_area"])

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
