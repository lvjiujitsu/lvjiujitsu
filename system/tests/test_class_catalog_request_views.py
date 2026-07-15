from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import (
    CategoryAudience,
    ClassCatalogRequestStatus,
    ClassCatalogRequestType,
    ClassCategory,
    ClassGroup,
    Person,
    PersonType,
    PortalAccount,
)
from system.services import PORTAL_ACCOUNT_SESSION_KEY
from system.services.class_requests import create_existing_teacher_class_request


class ClassCatalogRequestViewPermissionTestCase(TestCase):
    def setUp(self):
        self.instructor_type = PersonType.objects.create(
            code=PersonTypeCode.INSTRUCTOR,
            display_name="Professor",
        )
        self.admin_type = PersonType.objects.create(
            code=PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            display_name="Administrativo",
        )
        self.category = ClassCategory.objects.create(
            code="adult-view-requests",
            display_name="Adulto View Solicitações",
            audience=CategoryAudience.ADULT,
        )
        self.instructor = Person.objects.create(
            full_name="Professor Solicitante",
            cpf="744.126.528-23",
            person_type=self.instructor_type,
            birth_date=date(1988, 1, 1),
        )
        self.instructor_account = PortalAccount.objects.create(
            person=self.instructor, password_hash="hash"
        )
        self.manager = Person.objects.create(
            full_name="Gestor de Turmas",
            cpf="353.769.401-60",
            person_type=self.admin_type,
            birth_date=date(1980, 1, 1),
        )
        self.manager_account = PortalAccount.objects.create(
            person=self.manager, password_hash="hash"
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Jiu Jitsu View",
            class_category=self.category,
            main_teacher=self.instructor,
            default_capacity=20,
        )
        self.request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_SCHEDULE,
            class_group=self.class_group,
            class_category=None,
            display_name="",
            weekday="monday",
            training_style="mixed",
            start_time=time(20, 0),
            duration_minutes=60,
            default_capacity=20,
            justification="Abrir horário à noite.",
        )

    def _login(self, account):
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

    def test_manager_can_open_queue_and_detail(self):
        self._login(self.manager_account)

        list_response = self.client.get(reverse("system:class-catalog-request-list"))
        detail_response = self.client.get(
            reverse("system:class-catalog-request-detail", kwargs={"pk": self.request.pk})
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_detail_shows_operational_financial_arrangement(self):
        self.request.payload = {
            "payout": {
                "method": "pix",
                "pix_key_type": "cpf",
                "pix_key": "744.126.528-23",
                "financial_arrangement": "paid_fixed",
                "fixed_amount": "300.00",
                "student_percentage": "",
            }
        }
        self.request.save(update_fields=("payload", "updated_at"))
        self._login(self.manager_account)

        response = self.client.get(
            reverse("system:class-catalog-request-detail", kwargs={"pk": self.request.pk})
        )

        self.assertContains(response, "Condição: Valor fixo")
        self.assertContains(response, "R$ 300,00")

    def test_instructor_without_manage_capability_is_blocked_from_queue_and_detail(self):
        self._login(self.instructor_account)

        list_response = self.client.get(reverse("system:class-catalog-request-list"))
        detail_response = self.client.get(
            reverse("system:class-catalog-request-detail", kwargs={"pk": self.request.pk})
        )

        self.assertEqual(list_response.status_code, 302)
        self.assertEqual(detail_response.status_code, 302)

    def test_instructor_cannot_approve_via_post(self):
        self._login(self.instructor_account)

        response = self.client.post(
            reverse("system:class-catalog-request-detail", kwargs={"pk": self.request.pk}),
            data={"action": "approve"},
        )

        self.assertEqual(response.status_code, 302)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, ClassCatalogRequestStatus.PENDING)

    def test_requester_can_self_cancel(self):
        self._login(self.instructor_account)

        response = self.client.post(
            reverse("system:class-catalog-request-self-cancel", kwargs={"pk": self.request.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, ClassCatalogRequestStatus.CANCELED)

    def test_unrelated_person_cannot_self_cancel(self):
        other_instructor = Person.objects.create(
            full_name="Outro Professor",
            cpf="049.653.422-08",
            person_type=self.instructor_type,
            birth_date=date(1990, 1, 1),
        )
        other_account = PortalAccount.objects.create(
            person=other_instructor, password_hash="hash"
        )
        self._login(other_account)

        response = self.client.post(
            reverse("system:class-catalog-request-self-cancel", kwargs={"pk": self.request.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, ClassCatalogRequestStatus.PENDING)

    def test_public_new_teacher_create_redirects_to_main_registration_wizard(self):
        response = self.client.get(reverse("system:class-catalog-request-public-teacher-create"))

        self.assertRedirects(
            response,
            f"{reverse('system:register')}?profile=teacher_request",
            fetch_redirect_response=False,
        )
