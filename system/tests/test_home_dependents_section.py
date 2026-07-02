from datetime import date

from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import BiologicalSex, Person, PersonType, PortalAccount
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.services import PORTAL_ACCOUNT_SESSION_KEY


class HomeDependentsSectionTestCase(TestCase):
    """PRD-105: seção 'Meus dependentes' no home do responsável."""

    def setUp(self):
        self.guardian_type = PersonType.objects.create(
            code=PersonTypeCode.GUARDIAN,
            display_name="Responsável",
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.guardian = Person.objects.create(
            full_name="Responsável Fundacao Dependentes",
            cpf="390.533.447-05",
            person_type=self.guardian_type,
            birth_date=date(1980, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        self.dependent = Person.objects.create(
            full_name="Dependente Fundacao Dependentes",
            cpf="529.982.247-25",
            person_type=self.student_type,
            birth_date=date(2012, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        PersonRelationship.objects.create(
            source_person=self.guardian,
            target_person=self.dependent,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )

    def test_guardian_home_shows_dependents_section(self):
        self._login_as(self.guardian)
        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Meus dependentes", content)
        self.assertIn("Dependente Fundacao Dependentes", content)

    def test_person_without_dependents_has_no_section(self):
        self._login_as(self.dependent)
        response = self.client.get(reverse("system:home"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Meus dependentes", content)

    def _login_as(self, person):
        account = PortalAccount(person=person)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()
