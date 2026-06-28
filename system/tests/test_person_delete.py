from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
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
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PortalAccount,
)
from system.services import TECHNICAL_ADMIN_SESSION_KEY


class PersonDeleteViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin-pessoas",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.student_type = PersonType.objects.create(
            code=PersonTypeCode.STUDENT,
            display_name="Aluno",
        )
        self.guardian_type = PersonType.objects.create(
            code=PersonTypeCode.GUARDIAN,
            display_name="Responsável",
        )
        self.instructor_type = PersonType.objects.create(
            code=PersonTypeCode.INSTRUCTOR,
            display_name="Professor",
        )
        self.adult_category = ClassCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
        )
        IbjjfAgeCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
            minimum_age=18,
            display_order=1,
        )

    def test_student_delete_cascades_portal_account_enrollment_and_relationships(self):
        class_group = ClassGroup.objects.create(
            display_name="Adulto Noite",
            class_category=self.adult_category,
        )
        student = Person.objects.create(
            full_name="Aluno Sem Proteção",
            cpf="111.111.111-11",
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            person_type=self.student_type,
        )
        guardian = Person.objects.create(
            full_name="Responsável do Aluno",
            cpf="222.222.222-22",
            person_type=self.guardian_type,
        )
        PortalAccount.objects.create(person=student, password_hash="hash")
        ClassEnrollment.objects.create(class_group=class_group, person=student)
        PersonRelationship.objects.create(
            source_person=guardian,
            target_person=student,
            relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
        )
        student_pk = student.pk
        guardian_pk = guardian.pk
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:person-delete", kwargs={"pk": student_pk})
        )

        self.assertRedirects(response, reverse("system:person-list"))
        self.assertFalse(Person.objects.filter(pk=student_pk).exists())
        self.assertTrue(Person.objects.filter(pk=guardian_pk).exists())
        self.assertFalse(PortalAccount.objects.filter(person_id=student_pk).exists())
        self.assertFalse(ClassEnrollment.objects.filter(person_id=student_pk).exists())
        self.assertFalse(
            PersonRelationship.objects.filter(target_person_id=student_pk).exists()
        )
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Aluno Sem Proteção foi excluído(a) com sucesso.", messages)

    def test_person_delete_protected_by_class_group_redirects_with_message(self):
        teacher = Person.objects.create(
            full_name="Professor Protegido",
            cpf="333.333.333-33",
            person_type=self.instructor_type,
        )
        ClassGroup.objects.create(
            display_name="Adulto Professor",
            class_category=self.adult_category,
            main_teacher=teacher,
        )
        self._login_technical_admin()

        response = self.client.post(
            reverse("system:person-delete", kwargs={"pk": teacher.pk})
        )

        self.assertRedirects(
            response,
            reverse("system:person-detail", kwargs={"pk": teacher.pk}),
        )
        self.assertTrue(Person.objects.filter(pk=teacher.pk).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn(
            (
                "Não foi possível excluir Professor Protegido porque há vínculo "
                "protegido em turma principal. Remova ou substitua esse vínculo antes "
                "de excluir."
            ),
            messages,
        )

    def _login_technical_admin(self):
        session = self.client.session
        session[TECHNICAL_ADMIN_SESSION_KEY] = self.admin_user.pk
        session.save()
