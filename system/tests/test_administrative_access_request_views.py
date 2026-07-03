from datetime import date

from django.test import TestCase
from django.urls import reverse

from system.constants import OperationalRoleCode, PersonTypeCode, PortalCapability
from system.models import (
    AdministrativeAccessRequestOrigin,
    AdministrativeAccessRequestStatus,
    OperationalRole,
    Person,
    PersonType,
    PortalAccount,
)
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.access_requests import create_administrative_access_request


class AdministrativeAccessRequestViewPermissionTestCase(TestCase):
    def setUp(self):
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.admin_type = PersonType.objects.create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            display_name="Administrativo",
        )
        self.people_support_role = OperationalRole.objects.create(
            code=OperationalRoleCode.PEOPLE_SUPPORT,
            display_name="Apoio de pessoas",
            capabilities=[PortalCapability.SUPPORT_PEOPLE],
        )
        self.manager = Person.objects.create(
            full_name="Gestora de Pessoas",
            cpf="744.126.528-23",
            person_type=self.admin_type,
            birth_date=date(1985, 1, 1),
        )
        self.manager_account = PortalAccount.objects.create(
            person=self.manager, password_hash="hash"
        )
        self.student = Person.objects.create(
            full_name="Aluno Comum",
            cpf="353.769.401-60",
            person_type=self.student_type,
            birth_date=date(1997, 1, 1),
        )
        self.student_account = PortalAccount.objects.create(
            person=self.student, password_hash="hash"
        )
        self.request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PORTAL,
            full_name=self.student.full_name,
            cpf=self.student.cpf,
            email="aluno@example.com",
            phone="11900000000",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Preciso de acesso.",
            requester=self.student,
        )

    def _login(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_manager_can_open_queue_and_detail(self):
        self._login(self.manager_account)

        list_response = self.client.get(reverse("system:administrative-access-request-list"))
        detail_response = self.client.get(
            reverse("system:administrative-access-request-detail", kwargs={"pk": self.request.pk})
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_non_manager_is_blocked_from_queue_and_detail(self):
        self._login(self.student_account)

        list_response = self.client.get(reverse("system:administrative-access-request-list"))
        detail_response = self.client.get(
            reverse("system:administrative-access-request-detail", kwargs={"pk": self.request.pk})
        )

        self.assertEqual(list_response.status_code, 302)
        self.assertEqual(detail_response.status_code, 302)

    def test_non_manager_cannot_approve_via_post(self):
        self._login(self.student_account)

        response = self.client.post(
            reverse("system:administrative-access-request-detail", kwargs={"pk": self.request.pk}),
            data={"action": "approve", "approved_roles": [self.people_support_role.pk]},
        )

        self.assertEqual(response.status_code, 302)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, AdministrativeAccessRequestStatus.PENDING)

    def test_requester_can_self_cancel(self):
        self._login(self.student_account)

        response = self.client.post(
            reverse(
                "system:administrative-access-request-self-cancel",
                kwargs={"pk": self.request.pk},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, AdministrativeAccessRequestStatus.CANCELED)

    def test_unrelated_person_cannot_self_cancel(self):
        other_student = Person.objects.create(
            full_name="Outro Aluno",
            cpf="049.653.422-08",
            person_type=self.student_type,
            birth_date=date(1998, 1, 1),
        )
        other_account = PortalAccount.objects.create(person=other_student, password_hash="hash")
        self._login(other_account)

        response = self.client.post(
            reverse(
                "system:administrative-access-request-self-cancel",
                kwargs={"pk": self.request.pk},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, AdministrativeAccessRequestStatus.PENDING)

    def test_date_filter_narrows_queue(self):
        self._login(self.manager_account)

        response = self.client.get(
            reverse("system:administrative-access-request-list"),
            data={"date_from": "2999-01-01"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.request, list(response.context["access_requests"]))

    def test_public_create_redirects_to_main_registration_wizard(self):
        response = self.client.get(
            reverse("system:administrative-access-public-create"),
            data={
                "training_intent": "student",
                "compensation_preference": "barter",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('system:register')}?profile=administrative_request",
            fetch_redirect_response=False,
        )
