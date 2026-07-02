from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import PersonTypeCode
from system.models import (
    AuditAction,
    AuditModule,
    BiologicalSex,
    OperationalAuditEntry,
    Person,
    PersonType,
)
from system.services import TECHNICAL_ADMIN_SESSION_KEY, PORTAL_ACCOUNT_SESSION_KEY
from system.services.audit import record_audit_event


class OperationalAuditEntryModelTestCase(TestCase):
    def test_str_includes_module_action_and_entity(self):
        entry = record_audit_event(
            module=AuditModule.PERSON,
            action=AuditAction.CREATE,
            actor_label="Admin",
            entity_label="Fulano de Tal",
        )
        self.assertIn("Pessoas", str(entry))
        self.assertIn("Fulano de Tal", str(entry))


class PersonCrudWritesAuditEntryTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-audit",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()

    def test_person_create_writes_audit_entry(self):
        response = self.client.post(
            reverse("system:person-create"),
            data={
                "full_name": "Pessoa Auditoria",
                "cpf": "390.533.447-05",
                "birth_date": "1990-01-01",
                "biological_sex": BiologicalSex.MALE.value,
                "person_type": self.student_type.pk,
                "has_martial_art": "no",
                "is_active": "on",
                "payroll_payment_day": "28",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            OperationalAuditEntry.objects.filter(
                module=AuditModule.PERSON,
                action=AuditAction.CREATE,
                entity_label="Pessoa Auditoria",
            ).exists()
        )

    def test_person_delete_writes_audit_entry(self):
        person = Person.objects.create(
            full_name="Pessoa Para Excluir",
            cpf="529.982.247-25",
            person_type=self.student_type,
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        response = self.client.post(
            reverse("system:person-delete", kwargs={"pk": person.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            OperationalAuditEntry.objects.filter(
                module=AuditModule.PERSON,
                action=AuditAction.DELETE,
                entity_label="Pessoa Para Excluir",
            ).exists()
        )


class AuditLogListPermissionTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-audit-list",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        record_audit_event(
            module=AuditModule.FINANCIAL,
            action=AuditAction.MARK_PAID,
            actor_label="Admin",
            entity_label="Pedido #1",
        )

    def test_audit_list_requires_manage_academy(self):
        student = Person.objects.create(
            full_name="Aluno Sem Gestao",
            cpf="390.533.447-05",
            person_type=self.student_type,
            birth_date=date(1995, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        from system.models import PortalAccount

        account = PortalAccount(person=student)
        account.set_password("123456")
        account.save()
        session = self.client.session
        session[PORTAL_ACCOUNT_SESSION_KEY] = account.pk
        session.save()

        response = self.client.get(reverse("system:audit-log-list"))
        self.assertEqual(response.status_code, 302)

    def test_audit_list_renders_for_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()

        response = self.client.get(reverse("system:audit-log-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pedido #1")
