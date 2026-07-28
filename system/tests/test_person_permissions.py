from datetime import date

from django.test import TestCase
from django.urls import reverse

from system.constants import (
    OperationalRoleCode,
    PersonTypeCode,
    PortalCapability,
)
from system.models import (
    BiologicalSex,
    OperationalRole,
    Person,
    PersonOperationalRole,
    PersonType,
    PortalAccount,
)
from system.services import PORTAL_ACCOUNT_SESSION_KEY


class PersonUpdatePermissionMatrixTestCase(TestCase):

    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.admin_type = PersonType.objects.create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            display_name="Administrativo",
        )
        self.instructor_type = PersonType.objects.create(
            code=PersonTypeCode.INSTRUCTOR,
            display_name="Professor",
        )
        self.people_support_role = OperationalRole.objects.create(
            code=OperationalRoleCode.PEOPLE_SUPPORT,
            display_name="Apoio de pessoas",
            capabilities=[PortalCapability.SUPPORT_PEOPLE],
        )
        self.student = Person.objects.create(
            full_name="Aluno Fundacao Permissao",
            cpf="111.222.333-44",
            person_type=self.student_type,
            birth_date=date(1995, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        self.administrative_person = Person.objects.create(
            full_name="Administrativo Fundacao Permissao",
            cpf="555.666.777-88",
            person_type=self.admin_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        self.instructor = Person.objects.create(
            full_name="Instrutor Apoio Pessoas",
            cpf="222.333.444-55",
            person_type=self.instructor_type,
            birth_date=date(1988, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        PersonOperationalRole.objects.create(
            person=self.instructor,
            role=self.people_support_role,
        )
        self._login_as(self.instructor)

    def test_support_people_can_update_student(self):
        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": self.student.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_support_people_cannot_update_administrative_person(self):
        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": self.administrative_person.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_support_people_form_hides_payroll_fields(self):
        response = self.client.get(
            reverse("system:person-update", kwargs={"pk": self.student.pk})
        )
        self.assertFalse(response.context["form"].show_payroll_fields)
        self.assertNotContains(response, "Repasse do professor")

    def _login_as(self, person):
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()
