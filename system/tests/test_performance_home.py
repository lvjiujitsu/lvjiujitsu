from datetime import date

from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    Membership,
    MembershipStatus,
    Person,
    PersonType,
    PortalAccount,
    SubscriptionPlan,
)
from system.models.category import CategoryAudience
from system.models.graduation import BeltRank, Graduation
from system.models.person import PersonRelationship, PersonRelationshipKind
from system.models.plan import BillingCycle, PlanPaymentMethod
from system.services import PORTAL_ACCOUNT_SESSION_KEY


class HomeQueryBudgetTestCase(TestCase):
    STUDENT_HOME_MAX_QUERIES = 36
    GUARDIAN_WITH_THREE_DEPENDENTS_MAX_QUERIES = 90

    @classmethod
    def setUpTestData(cls):
        cls.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        cls.guardian_type = PersonType.objects.create(
            code=PersonTypeCode.GUARDIAN,
            display_name="Responsável",
        )
        cls.plan = SubscriptionPlan.objects.create(
            code="home-budget-plan",
            display_name="Plano home budget",
            billing_cycle=BillingCycle.MONTHLY,
            payment_method=PlanPaymentMethod.PIX,
            price=0,
        )
        belt = BeltRank.objects.create(
            code="home-budget-white",
            display_name="Branca",
            audience=CategoryAudience.ADULT,
            color_hex="#ffffff",
            display_order=1,
        )
        cls.student = Person.objects.create(
            full_name="Aluno Home Budget",
            cpf="920.100.000-01",
            person_type=cls.student_type,
            birth_date=date(2000, 1, 1),
            biological_sex=BiologicalSex.MALE,
            jiu_jitsu_belt="white",
        )
        Graduation.objects.create(
            person=cls.student,
            belt_rank=belt,
            grade_number=0,
            awarded_at=date(2025, 1, 1),
        )
        cls.student_account = PortalAccount(person=cls.student)
        cls.student_account.set_password("123456")
        cls.student_account.save()
        Membership.objects.create(
            person=cls.student,
            plan=cls.plan,
            status=MembershipStatus.ACTIVE,
        )

        cls.guardian = Person.objects.create(
            full_name="Responsável Home Budget",
            cpf="920.100.000-02",
            person_type=cls.guardian_type,
            birth_date=date(1985, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
        )
        cls.guardian_account = PortalAccount(person=cls.guardian)
        cls.guardian_account.set_password("123456")
        cls.guardian_account.save()
        Membership.objects.create(
            person=cls.guardian,
            plan=cls.plan,
            status=MembershipStatus.ACTIVE,
        )
        for index in range(1, 4):
            dependent = Person.objects.create(
                full_name=f"Dependente Home Budget {index}",
                cpf=f"920.100.00{index}-0{index}",
                person_type=cls.student_type,
                birth_date=date(2012, index, 1),
                biological_sex=BiologicalSex.MALE,
                jiu_jitsu_belt="white",
            )
            Graduation.objects.create(
                person=dependent,
                belt_rank=belt,
                grade_number=0,
                awarded_at=date(2025, 1, 1),
            )
            PersonRelationship.objects.create(
                source_person=cls.guardian,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            )
            Membership.objects.create(
                person=dependent,
                plan=cls.plan,
                status=MembershipStatus.ACTIVE,
            )

    def _login(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_student_home_query_budget(self):
        self._login(self.student_account)
        with self.assertNumQueries(self.STUDENT_HOME_MAX_QUERIES):
            response = self.client.get(reverse("system:home"))
        self.assertEqual(response.status_code, 200)

    def test_guardian_with_three_dependents_home_query_budget(self):
        self._login(self.guardian_account)
        with self.assertNumQueries(self.GUARDIAN_WITH_THREE_DEPENDENTS_MAX_QUERIES):
            response = self.client.get(reverse("system:home"))
        self.assertEqual(response.status_code, 200)
