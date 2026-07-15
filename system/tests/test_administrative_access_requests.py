from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from system.constants import OperationalRoleCode, PersonTypeCode, PortalCapability
from system.models import (
    AdministrativeAccessRequest,
    AdministrativeAccessRequestOrigin,
    AdministrativeAccessRequestStatus,
    OperationalRole,
    Person,
    PersonOperationalRole,
    PersonType,
    PortalAccount,
)
from system.services.access_requests import (
    approve_administrative_access_request,
    cancel_administrative_access_request,
    create_administrative_access_request,
    reject_administrative_access_request,
)


class AdministrativeAccessRequestServiceTestCase(TestCase):
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
        self.academy_manager_role = OperationalRole.objects.create(
            code=OperationalRoleCode.ACADEMY_MANAGER,
            display_name="Gestor da academia",
            capabilities=[PortalCapability.MANAGE_ACADEMY],
        )
        self.approver = Person.objects.create(
            full_name="Admin Aprovador",
            cpf="100.000.000-00",
            person_type=self.admin_type,
            birth_date=date(1980, 1, 1),
        )

    def test_public_administrative_request_does_not_create_person(self):
        create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Solicitante Administrativo",
            cpf="11144477735",
            email="admin.request@example.com",
            phone="11999990000",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Preciso apoiar o cadastro de pessoas.",
            password="SenhaForte123",
        )

        self.assertEqual(Person.objects.exclude(pk=self.approver.pk).count(), 0)
        request = AdministrativeAccessRequest.objects.get(cpf="111.444.777-35")
        self.assertEqual(request.status, AdministrativeAccessRequestStatus.PENDING)
        self.assertIsNone(request.person)

    def test_public_request_stores_training_and_compensation_payload(self):
        create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Aluno Administrativo",
            cpf="11144477735",
            email="aluno.admin@example.com",
            phone="11999990001",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Vou apoiar a recepção e treinar.",
            password="SenhaForte123",
            request_payload={
                "training_intent": "student",
                "compensation_preference": "pix",
                "pix_key_type": "CPF",
                "pix_key": "111.444.777-35",
            },
        )

        request = AdministrativeAccessRequest.objects.get(cpf="111.444.777-35")
        self.assertEqual(request.request_payload["training_intent"], "student")
        self.assertEqual(request.request_payload["compensation_preference"], "pix")
        self.assertEqual(request.request_payload["pix_key_type"], "CPF")
        self.assertEqual(request.request_payload["pix_key"], "111.444.777-35")

    def test_duplicate_pending_request_for_same_cpf_is_rejected(self):
        create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Solicitante Administrativo",
            cpf="11144477735",
            email="admin.request@example.com",
            phone="11999990000",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Primeira solicitação.",
            password="SenhaForte123",
        )

        with self.assertRaises(ValidationError):
            create_administrative_access_request(
                origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
                full_name="Solicitante Administrativo",
                cpf="111.444.777-35",
                email="admin.request@example.com",
                phone="11999990000",
                requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
                justification="Solicitação duplicada.",
                password="SenhaForte123",
            )

    def test_approve_operational_roles_keeps_existing_person_type(self):
        student = Person.objects.create(
            full_name="Aluno com Upgrade",
            cpf="529.982.247-25",
            person_type=self.student_type,
            birth_date=date(1995, 5, 5),
        )
        PortalAccount.objects.create(person=student, password_hash="hash")
        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PORTAL,
            full_name=student.full_name,
            cpf=student.cpf,
            email="aluno.upgrade@example.com",
            phone="11988887777",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Apoio temporário de secretaria.",
            requester=student,
        )

        approve_administrative_access_request(
            request.pk,
            approved_by=self.approver,
            approved_role_ids=[self.people_support_role.pk],
            grant_full_administrative=False,
            decision_notes="Aprovado como apoio.",
        )

        student.refresh_from_db()
        request.refresh_from_db()
        self.assertEqual(student.person_type, self.student_type)
        self.assertEqual(request.status, AdministrativeAccessRequestStatus.APPROVED)
        self.assertTrue(
            PersonOperationalRole.objects.filter(
                person=student,
                role=self.people_support_role,
                is_active=True,
            ).exists()
        )

    def test_approve_public_student_intent_creates_student_with_operational_role(self):
        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Aluno Administrativo Novo",
            cpf="71320260705",
            email="student.admin@example.com",
            phone="11970000007",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Treinar e apoiar o cadastro de pessoas.",
            password="SenhaForte123",
            request_payload={"training_intent": "student"},
        )

        approve_administrative_access_request(
            request.pk,
            approved_by=self.approver,
            approved_role_ids=[self.people_support_role.pk],
            grant_full_administrative=False,
        )

        person = Person.objects.get(cpf="713.202.607-05")
        self.assertEqual(person.person_type, self.student_type)
        self.assertTrue(person.access_account.check_password("SenhaForte123"))
        self.assertTrue(
            PersonOperationalRole.objects.filter(
                person=person,
                role=self.people_support_role,
                is_active=True,
            ).exists()
        )

    def test_approve_full_administrative_creates_person_and_account(self):
        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Novo Administrativo",
            cpf="93541134780",
            email="novo.admin@example.com",
            phone="11977776666",
            requested_role_codes=[OperationalRoleCode.ACADEMY_MANAGER],
            justification="Gestão completa da unidade.",
            password="SenhaForte123",
        )

        approve_administrative_access_request(
            request.pk,
            approved_by=self.approver,
            approved_role_ids=[],
            grant_full_administrative=True,
            decision_notes="Acesso pleno aprovado.",
        )

        person = Person.objects.get(cpf="935.411.347-80")
        self.assertEqual(person.person_type, self.admin_type)
        self.assertTrue(person.access_account.check_password("SenhaForte123"))
        request.refresh_from_db()
        self.assertEqual(request.approved_person, person)

    def test_reject_request_keeps_person_unchanged(self):
        student = Person.objects.create(
            full_name="Aluno Reprovado",
            cpf="390.533.447-05",
            person_type=self.student_type,
            birth_date=date(1994, 4, 4),
        )
        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PORTAL,
            full_name=student.full_name,
            cpf=student.cpf,
            email="aluno.reprovado@example.com",
            phone="11966665555",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Solicitação sem escopo.",
            requester=student,
        )

        reject_administrative_access_request(
            request.pk,
            rejected_by=self.approver,
            decision_notes="Sem necessidade operacional.",
        )

        request.refresh_from_db()
        self.assertEqual(request.status, AdministrativeAccessRequestStatus.REJECTED)
        self.assertFalse(PersonOperationalRole.objects.filter(person=student).exists())

    def test_existing_person_request_links_by_cpf_without_duplicate(self):
        student = Person.objects.create(
            full_name="Aluno Existente",
            cpf="744.126.528-23",
            person_type=self.student_type,
            birth_date=date(1996, 6, 6),
        )

        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Aluno Existente",
            cpf="744.126.528-23",
            email="aluno.existente@example.com",
            phone="11933332222",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Já sou aluno e quero apoiar a secretaria.",
            password="SenhaForte123",
        )

        self.assertEqual(request.person, student)
        self.assertEqual(Person.objects.filter(cpf="744.126.528-23").count(), 1)

        approve_administrative_access_request(
            request.pk,
            approved_by=self.approver,
            approved_role_ids=[self.people_support_role.pk],
            grant_full_administrative=False,
        )

        self.assertEqual(Person.objects.filter(cpf="744.126.528-23").count(), 1)
        request.refresh_from_db()
        self.assertEqual(request.approved_person, student)

    def test_cancel_pending_request_by_requester(self):
        student = Person.objects.create(
            full_name="Aluno Cancelador",
            cpf="353.769.401-60",
            person_type=self.student_type,
            birth_date=date(1993, 3, 3),
        )
        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PORTAL,
            full_name=student.full_name,
            cpf=student.cpf,
            email="aluno.cancelador@example.com",
            phone="11922221111",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Mudei de ideia.",
            requester=student,
        )

        cancel_administrative_access_request(request.pk, canceled_by=student)

        request.refresh_from_db()
        self.assertEqual(request.status, AdministrativeAccessRequestStatus.CANCELED)
        self.assertEqual(request.decided_by, student)

    def test_cannot_cancel_already_decided_request(self):
        request = create_administrative_access_request(
            origin=AdministrativeAccessRequestOrigin.PUBLIC_REGISTRATION,
            full_name="Solicitante Decidido",
            cpf="049.653.422-08",
            email="decidido@example.com",
            phone="11911110000",
            requested_role_codes=[OperationalRoleCode.PEOPLE_SUPPORT],
            justification="Solicitação já decidida.",
            password="SenhaForte123",
        )
        reject_administrative_access_request(
            request.pk,
            rejected_by=self.approver,
            decision_notes="Sem necessidade.",
        )

        with self.assertRaises(ValidationError):
            cancel_administrative_access_request(request.pk, canceled_by=self.approver)
