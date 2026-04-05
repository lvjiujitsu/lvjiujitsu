import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from system.forms import PortalRegistrationForm
from system.models import (
    BiologicalSex,
    ClassEnrollment,
    ClassGroup,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PortalAccount,
    PortalPasswordResetToken,
)
from system.services.seeding import seed_class_catalog


User = get_user_model()


class PersonModelTestCase(TestCase):
    def test_person_has_single_type(self):
        student_type = PersonType.objects.create(
            code="student-test",
            display_name="Aluno teste",
        )
        person = Person.objects.create(
            full_name="Maria Souza",
            cpf="123.456.789-00",
            person_type=student_type,
        )

        self.assertEqual(person.person_type, student_type)
        self.assertTrue(person.has_type_code("student-test"))
        self.assertEqual(str(person), "Maria Souza")

    def test_portal_account_is_independent_from_django_user(self):
        person = Person.objects.create(
            full_name="Carlos Silva",
            cpf="123.456.789-01",
        )
        access_account = PortalAccount(person=person)
        access_account.set_password("SenhaForte@123")
        access_account.save()

        self.assertTrue(access_account.check_password("SenhaForte@123"))
        self.assertEqual(User.objects.count(), 0)

    def test_holder_registration_form_creates_local_accounts(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "include_dependent": "on",
                "holder_name": "Carlos Titular",
                "holder_cpf": "12345678901",
                "holder_birthdate": "01/01/1990",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_phone": "(62) 99999-1111",
                "holder_email": "carlos@example.com",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "dependent_name": "João Dependente",
                "dependent_cpf": "12345678902",
                "dependent_birthdate": "02/02/2015",
                "dependent_biological_sex": BiologicalSex.MALE,
                "dependent_password": "123456",
                "dependent_password_confirm": "123456",
                "dependent_kinship_type": "father",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        holder = created["holder"]
        dependent = created["dependent"]

        self.assertEqual(holder.person_type.code, "student")
        self.assertEqual(holder.access_account.person, holder)
        self.assertTrue(holder.access_account.check_password("123456"))
        self.assertEqual(dependent.person_type.code, "dependent")
        self.assertEqual(dependent.access_account.person, dependent)
        self.assertTrue(dependent.access_account.check_password("123456"))
        self.assertTrue(
            PersonRelationship.objects.filter(
                source_person=holder,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )
        self.assertEqual(User.objects.count(), 0)

    def test_guardian_registration_form_creates_guardian_and_dependent_accounts(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "guardian",
                "guardian_name": "Paula Responsável",
                "guardian_cpf": "98765432100",
                "guardian_phone": "(62) 99999-3333",
                "guardian_email": "paula@example.com",
                "guardian_password": "123456",
                "guardian_password_confirm": "123456",
                "student_name": "Pedro Aluno",
                "student_cpf": "98765432101",
                "student_birthdate": "03/03/2012",
                "student_biological_sex": BiologicalSex.MALE,
                "student_password": "123456",
                "student_password_confirm": "123456",
                "student_kinship_type": "mother",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        guardian = created["guardian"]
        student = created["student"]

        self.assertEqual(guardian.person_type.code, "guardian")
        self.assertEqual(student.person_type.code, "dependent")
        self.assertTrue(guardian.access_account.check_password("123456"))
        self.assertTrue(student.access_account.check_password("123456"))

    def test_registration_form_requires_matching_password_confirmation(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Carlos Titular",
                "holder_cpf": "12345678901",
                "holder_birthdate": "01/01/1990",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "654321",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("holder_password_confirm", form.errors)

    def test_password_reset_token_defaults_to_active_window(self):
        person = Person.objects.create(
            full_name="Carlos Silva",
            cpf="123.456.789-01",
            email="carlos@example.com",
        )
        access_account = PortalAccount(person=person)
        access_account.set_password("123456")
        access_account.save()

        reset_token = PortalPasswordResetToken.objects.create(access_account=access_account)

        self.assertTrue(reset_token.is_valid())
        self.assertGreater(reset_token.expires_at, timezone.now())

    def test_registration_creates_multiple_class_enrollments_from_selected_groups(self):
        seed_class_catalog()
        primary_group = ClassGroup.objects.get(code="adult-lauro")
        secondary_group = ClassGroup.objects.get(code="adult-layon")

        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Aluno com Turma",
                "holder_cpf": "22345678901",
                "holder_birthdate": "01/01/1995",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "holder_class_groups": [primary_group.pk, secondary_group.pk],
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()
        holder = created["holder"]

        self.assertEqual(holder.class_group, primary_group)
        self.assertIsNone(holder.class_schedule)
        self.assertEqual(holder.class_category, primary_group.class_category)
        self.assertEqual(ClassEnrollment.objects.filter(person=holder).count(), 2)

    def test_guardian_registration_accepts_multiple_dependents(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "guardian",
                "guardian_name": "Responsável Multi",
                "guardian_cpf": "32345678901",
                "guardian_password": "123456",
                "guardian_password_confirm": "123456",
                "student_name": "Dependente Principal",
                "student_cpf": "32345678902",
                "student_birthdate": "01/02/2014",
                "student_biological_sex": BiologicalSex.FEMALE,
                "student_password": "123456",
                "student_password_confirm": "123456",
                "student_kinship_type": "mother",
                "extra_dependents_payload": json.dumps(
                    [
                        {
                            "full_name": "Dependente Extra 1",
                            "cpf": "32345678903",
                            "birth_date": "01/03/2015",
                            "biological_sex": BiologicalSex.FEMALE,
                            "password": "123456",
                            "password_confirm": "123456",
                            "kinship_type": "mother",
                        },
                        {
                            "full_name": "Dependente Extra 2",
                            "cpf": "32345678904",
                            "birth_date": "01/04/2016",
                            "biological_sex": BiologicalSex.MALE,
                            "password": "123456",
                            "password_confirm": "123456",
                            "kinship_type": "other",
                            "kinship_other_label": "Tutor legal",
                        },
                    ]
                ),
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        self.assertEqual(len(created["dependents"]), 3)
        self.assertEqual(
            PersonRelationship.objects.filter(
                source_person=created["guardian"],
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).count(),
            3,
        )

    def test_other_registration_creates_single_selected_type(self):
        PersonType.objects.create(code="instructor", display_name="Professor")
        form = PortalRegistrationForm(
            data={
                "registration_profile": "other",
                "other_type_code": "instructor",
                "other_name": "Professor Teste",
                "other_cpf": "42345678901",
                "other_birthdate": "01/01/1990",
                "other_password": "123456",
                "other_password_confirm": "123456",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        self.assertEqual(created["other"].person_type.code, "instructor")
