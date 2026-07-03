from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from system.constants import PersonTypeCode
from system.models import (
    CategoryAudience,
    ClassCatalogRequest,
    ClassCatalogRequestStatus,
    ClassCatalogRequestType,
    ClassCategory,
    ClassGroup,
    ClassInstructorAssignment,
    ClassSchedule,
    Person,
    PersonType,
    TeacherBankAccount,
)
from system.services.class_requests import (
    approve_class_catalog_request,
    cancel_class_catalog_request,
    create_existing_teacher_class_request,
    create_new_teacher_class_request,
    reject_class_catalog_request,
)


class ClassCatalogRequestServiceTestCase(TestCase):
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
            code="adult-requests",
            display_name="Adulto Solicitações",
            audience=CategoryAudience.ADULT,
        )
        self.other_category = ClassCategory.objects.create(
            code="kids-requests",
            display_name="Kids Solicitações",
            audience=CategoryAudience.KIDS,
        )
        self.instructor = Person.objects.create(
            full_name="Professor Solicitante",
            cpf="500.000.000-00",
            person_type=self.instructor_type,
            birth_date=date(1988, 1, 1),
        )
        self.other_instructor = Person.objects.create(
            full_name="Professor Outra Turma",
            cpf="500.000.000-01",
            person_type=self.instructor_type,
            birth_date=date(1988, 1, 2),
        )
        self.approver = Person.objects.create(
            full_name="Gestor de Turmas",
            cpf="500.000.000-02",
            person_type=self.admin_type,
            birth_date=date(1980, 1, 1),
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Jiu Jitsu",
            class_category=self.category,
            main_teacher=self.instructor,
            default_capacity=20,
        )
        self.unscoped_group = ClassGroup.objects.create(
            display_name="Jiu Jitsu Kids",
            class_category=self.other_category,
            main_teacher=self.other_instructor,
            default_capacity=15,
        )

    def test_instructor_request_new_schedule_does_not_create_schedule(self):
        request = create_existing_teacher_class_request(
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

        self.assertEqual(request.status, ClassCatalogRequestStatus.PENDING)
        self.assertNotIn("payout", request.payload)
        self.assertFalse(
            ClassSchedule.objects.filter(
                class_group=self.class_group,
                weekday="monday",
                start_time=time(20, 0),
            ).exists()
        )

    def test_approve_new_schedule_creates_class_schedule(self):
        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_SCHEDULE,
            class_group=self.class_group,
            class_category=None,
            display_name="",
            weekday="tuesday",
            training_style="gi",
            start_time=time(6, 30),
            duration_minutes=75,
            default_capacity=20,
            justification="Turma de manhã.",
        )

        approve_class_catalog_request(request.pk, approved_by=self.approver)

        request.refresh_from_db()
        self.assertEqual(request.status, ClassCatalogRequestStatus.APPROVED)
        self.assertTrue(
            ClassSchedule.objects.filter(
                class_group=self.class_group,
                weekday="tuesday",
                training_style="gi",
                start_time=time(6, 30),
                duration_minutes=75,
            ).exists()
        )

    def test_instructor_cannot_request_for_unscoped_class_group(self):
        with self.assertRaises(ValidationError):
            create_existing_teacher_class_request(
                requester=self.instructor,
                request_type=ClassCatalogRequestType.NEW_SCHEDULE,
                class_group=self.unscoped_group,
                class_category=None,
                display_name="",
                weekday="monday",
                training_style="mixed",
                start_time=time(19, 0),
                duration_minutes=60,
                default_capacity=15,
                justification="Horário fora da minha turma.",
            )

    def test_new_class_group_request_approval_creates_group_and_schedule(self):
        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_CLASS_GROUP,
            class_group=None,
            class_category=self.category,
            display_name="No-Gi",
            weekday="wednesday",
            training_style="no_gi",
            start_time=time(18, 30),
            duration_minutes=60,
            default_capacity=18,
            justification="Abrir turma sem kimono.",
        )

        approve_class_catalog_request(request.pk, approved_by=self.approver)

        request.refresh_from_db()
        created_group = request.created_class_group
        self.assertEqual(created_group.display_name, "No-Gi")
        self.assertEqual(created_group.main_teacher, self.instructor)
        self.assertTrue(
            created_group.schedules.filter(
                weekday="wednesday",
                training_style="no_gi",
                start_time=time(18, 30),
            ).exists()
        )

    def test_new_teacher_request_does_not_create_person_before_approval(self):
        create_new_teacher_class_request(
            full_name="Professor Novo",
            cpf="16899535009",
            email="professor.novo@example.com",
            phone="11955554444",
            password="SenhaForte123",
            class_category=self.category,
            display_name="Jiu Jitsu",
            weekday="thursday",
            training_style="mixed",
            start_time=time(7, 0),
            duration_minutes=60,
            default_capacity=16,
            justification="Proposta de horário inicial.",
        )

        self.assertFalse(Person.objects.filter(cpf="168.995.350-09").exists())

    def test_new_teacher_request_approval_creates_instructor_and_schedule(self):
        request = create_new_teacher_class_request(
            full_name="Professor Novo",
            cpf="16899535009",
            email="professor.novo@example.com",
            phone="11955554444",
            password="SenhaForte123",
            class_category=self.category,
            display_name="Jiu Jitsu Iniciante",
            weekday="friday",
            training_style="mixed",
            start_time=time(8, 0),
            duration_minutes=60,
            default_capacity=16,
            justification="Proposta de horário inicial.",
        )

        approve_class_catalog_request(request.pk, approved_by=self.approver)

        request.refresh_from_db()
        teacher = Person.objects.get(cpf="168.995.350-09")
        self.assertEqual(teacher.person_type, self.instructor_type)
        self.assertTrue(teacher.access_account.check_password("SenhaForte123"))
        self.assertEqual(request.created_teacher, teacher)
        self.assertEqual(request.created_class_group.main_teacher, teacher)

    def test_new_teacher_request_stores_pix_and_approval_creates_bank_account(self):
        request = create_new_teacher_class_request(
            full_name="Professor PIX",
            cpf="93541134780",
            email="professor.pix@example.com",
            phone="11955554445",
            password="SenhaForte123",
            class_category=self.category,
            display_name="Jiu Jitsu PIX",
            weekday="saturday",
            training_style="mixed",
            start_time=time(9, 0),
            duration_minutes=60,
            default_capacity=12,
            justification="Proposta com recebimento por PIX.",
            payout_data={
                "method": "pix",
                "pix_key_type": "CPF",
                "pix_key": "935.411.347-80",
                "holder_name": "Professor PIX",
                "holder_document": "935.411.347-80",
            },
        )

        self.assertEqual(request.payload["payout"]["method"], "pix")
        approve_class_catalog_request(request.pk, approved_by=self.approver)

        teacher = Person.objects.get(cpf="935.411.347-80")
        bank_account = TeacherBankAccount.objects.get(person=teacher)
        self.assertEqual(bank_account.pix_key_type, "CPF")
        self.assertEqual(bank_account.pix_key, "935.411.347-80")
        self.assertEqual(bank_account.holder_name, "Professor PIX")

    def test_reject_request_creates_no_catalog_records(self):
        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_CLASS_GROUP,
            class_group=None,
            class_category=self.category,
            display_name="Turma Recusada",
            weekday="saturday",
            training_style="mixed",
            start_time=time(10, 0),
            duration_minutes=60,
            default_capacity=12,
            justification="Sem agenda.",
        )

        reject_class_catalog_request(
            request.pk,
            rejected_by=self.approver,
            decision_notes="Sem sala disponível.",
        )

        request.refresh_from_db()
        self.assertEqual(request.status, ClassCatalogRequestStatus.REJECTED)
        self.assertFalse(ClassGroup.objects.filter(display_name="Turma Recusada").exists())

    def test_duplicate_schedule_conflict_is_blocked(self):
        ClassSchedule.objects.create(
            class_group=self.class_group,
            weekday="monday",
            training_style="mixed",
            start_time=time(19, 0),
            duration_minutes=60,
        )

        with self.assertRaises(ValidationError):
            create_existing_teacher_class_request(
                requester=self.instructor,
                request_type=ClassCatalogRequestType.NEW_SCHEDULE,
                class_group=self.class_group,
                class_category=None,
                display_name="",
                weekday="monday",
                training_style="mixed",
                start_time=time(19, 0),
                duration_minutes=60,
                default_capacity=20,
                justification="Conflito intencional.",
            )

    def test_assistant_teacher_can_request_scoped_class_group(self):
        ClassInstructorAssignment.objects.create(
            class_group=self.unscoped_group,
            person=self.instructor,
        )

        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_SCHEDULE,
            class_group=self.unscoped_group,
            class_category=None,
            display_name="",
            weekday="sunday",
            training_style="mixed",
            start_time=time(9, 0),
            duration_minutes=60,
            default_capacity=15,
            justification="Apoio docente na turma.",
        )

        self.assertEqual(request.status, ClassCatalogRequestStatus.PENDING)

    def test_cancel_pending_request_by_requester(self):
        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_SCHEDULE,
            class_group=self.class_group,
            class_category=None,
            display_name="",
            weekday="thursday",
            training_style="mixed",
            start_time=time(21, 0),
            duration_minutes=60,
            default_capacity=20,
            justification="Vou cancelar.",
        )

        cancel_class_catalog_request(request.pk, canceled_by=self.instructor)

        request.refresh_from_db()
        self.assertEqual(request.status, ClassCatalogRequestStatus.CANCELED)
        self.assertEqual(request.decided_by, self.instructor)

    def test_cannot_cancel_already_decided_request(self):
        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_SCHEDULE,
            class_group=self.class_group,
            class_category=None,
            display_name="",
            weekday="friday",
            training_style="mixed",
            start_time=time(21, 0),
            duration_minutes=60,
            default_capacity=20,
            justification="Já decidida.",
        )
        approve_class_catalog_request(request.pk, approved_by=self.approver)

        with self.assertRaises(ValidationError):
            cancel_class_catalog_request(request.pk, canceled_by=self.instructor)

    def test_new_class_group_request_with_extra_schedules_creates_all_slots(self):
        request = create_existing_teacher_class_request(
            requester=self.instructor,
            request_type=ClassCatalogRequestType.NEW_CLASS_GROUP,
            class_group=None,
            class_category=self.category,
            display_name="Fundamentos",
            weekday="monday",
            training_style="gi",
            start_time=time(19, 0),
            duration_minutes=60,
            default_capacity=20,
            justification="Turma com mais de um horário semanal.",
            extra_schedules=[
                {
                    "weekday": "wednesday",
                    "training_style": "gi",
                    "start_time": time(19, 0),
                    "duration_minutes": 60,
                },
                {
                    "weekday": "friday",
                    "training_style": "no_gi",
                    "start_time": time(20, 0),
                    "duration_minutes": 90,
                },
            ],
        )

        approve_class_catalog_request(request.pk, approved_by=self.approver)

        request.refresh_from_db()
        created_group = request.created_class_group
        self.assertEqual(created_group.schedules.count(), 3)
        self.assertTrue(
            created_group.schedules.filter(weekday="wednesday", training_style="gi").exists()
        )
        self.assertTrue(
            created_group.schedules.filter(
                weekday="friday", training_style="no_gi", duration_minutes=90
            ).exists()
        )

    def test_extra_schedule_duplicate_within_request_is_blocked(self):
        with self.assertRaises(ValidationError):
            create_existing_teacher_class_request(
                requester=self.instructor,
                request_type=ClassCatalogRequestType.NEW_CLASS_GROUP,
                class_group=None,
                class_category=self.category,
                display_name="Duplicada",
                weekday="monday",
                training_style="gi",
                start_time=time(19, 0),
                duration_minutes=60,
                default_capacity=20,
                justification="Horário repetido.",
                extra_schedules=[
                    {
                        "weekday": "monday",
                        "training_style": "gi",
                        "start_time": time(19, 0),
                        "duration_minutes": 60,
                    },
                ],
            )

    def test_extra_schedules_not_allowed_for_new_schedule_request(self):
        with self.assertRaises(ValidationError):
            create_existing_teacher_class_request(
                requester=self.instructor,
                request_type=ClassCatalogRequestType.NEW_SCHEDULE,
                class_group=self.class_group,
                class_category=None,
                display_name="",
                weekday="saturday",
                training_style="mixed",
                start_time=time(11, 0),
                duration_minutes=60,
                default_capacity=20,
                justification="Não pode ter extras.",
                extra_schedules=[
                    {
                        "weekday": "sunday",
                        "training_style": "mixed",
                        "start_time": time(11, 0),
                        "duration_minutes": 60,
                    },
                ],
            )
