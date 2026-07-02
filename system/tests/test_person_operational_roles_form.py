from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from system.constants import (
    OperationalRoleCode,
    PersonTypeCode,
)
from system.models import (
    BiologicalSex,
    ClassCategory,
    ClassGroup,
    Person,
    PersonOperationalRole,
    PersonType,
)
from system.models.category import CategoryAudience
from system.services import TECHNICAL_ADMIN_SESSION_KEY
from system.services.portal_capabilities import ensure_default_operational_roles


class PersonFormOperationalRolesTestCase(TestCase):
    """PRD-091: atribuir papeis operacionais (ex: apoio de turma) no cadastro de pessoa."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-lv-roles",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.category = ClassCategory.objects.create(
            code="kids-fundacao",
            display_name="Kids Fundacao",
            audience=CategoryAudience.KIDS,
        )
        self.class_group = ClassGroup.objects.create(
            display_name="Kids Fundacao Turma",
            class_category=self.category,
        )
        self.roles = ensure_default_operational_roles()
        self.miguel = Person.objects.create(
            full_name="Miguel Torres Dourado",
            cpf="920.000.012-62",
            person_type=self.student_type,
            birth_date=date(1990, 3, 14),
            biological_sex=BiologicalSex.MALE,
        )
        self._login_technical_admin()

    def test_assign_class_assistant_role_requires_class_group(self):
        response = self.client.post(
            reverse("system:person-update", kwargs={"pk": self.miguel.pk}),
            data=self._base_payload(operational_roles=[self.roles[OperationalRoleCode.CLASS_ASSISTANT].pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "class_assistant_group", "Selecione a turma para o apoio de turma.")

    def test_assign_class_assistant_role_with_class_group_succeeds(self):
        response = self.client.post(
            reverse("system:person-update", kwargs={"pk": self.miguel.pk}),
            data=self._base_payload(
                operational_roles=[self.roles[OperationalRoleCode.CLASS_ASSISTANT].pk],
                class_assistant_group=self.class_group.pk,
            ),
        )
        self.assertRedirects(response, reverse("system:person-list"))
        assignment = PersonOperationalRole.objects.get(
            person=self.miguel, role=self.roles[OperationalRoleCode.CLASS_ASSISTANT]
        )
        self.assertEqual(assignment.class_group_id, self.class_group.pk)

    def test_capabilities_reflect_new_role_after_save(self):
        self.client.post(
            reverse("system:person-update", kwargs={"pk": self.miguel.pk}),
            data=self._base_payload(
                operational_roles=[self.roles[OperationalRoleCode.CLASS_ASSISTANT].pk],
                class_assistant_group=self.class_group.pk,
            ),
        )
        self.miguel.refresh_from_db()
        active_codes = {
            assignment.role.code
            for assignment in self.miguel.operational_role_assignments.filter(is_active=True)
        }
        self.assertIn(OperationalRoleCode.CLASS_ASSISTANT, active_codes)

    def test_removing_role_deletes_assignment(self):
        PersonOperationalRole.objects.create(
            person=self.miguel,
            role=self.roles[OperationalRoleCode.CLASS_ASSISTANT],
            class_group=self.class_group,
        )
        response = self.client.post(
            reverse("system:person-update", kwargs={"pk": self.miguel.pk}),
            data=self._base_payload(operational_roles=[]),
        )
        self.assertRedirects(response, reverse("system:person-list"))
        self.assertFalse(
            PersonOperationalRole.objects.filter(person=self.miguel).exists()
        )

    def _base_payload(self, operational_roles=None, class_assistant_group=""):
        payload = {
            "full_name": "Miguel Torres Dourado",
            "cpf": "920.000.012-62",
            "birth_date": "1990-03-14",
            "biological_sex": BiologicalSex.MALE.value,
            "person_type": self.student_type.pk,
            "has_martial_art": "no",
            "is_active": "on",
            "payroll_payment_day": "28",
            "class_assistant_group": class_assistant_group,
        }
        for role_pk in operational_roles or []:
            payload.setdefault("operational_roles", []).append(str(role_pk))
        return payload

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
