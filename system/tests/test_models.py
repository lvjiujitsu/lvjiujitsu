import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from system.forms import PortalRegistrationForm
from system.models import (
    ClassGroup,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PortalAccount,
    PortalPasswordResetToken,
)
from system.services.seeding import seed_class_catalog, seed_person_matrix


User = get_user_model()


class PersonModelTestCase(TestCase):
    def test_person_can_have_multiple_types(self):
        student_type = PersonType.objects.create(
            code="student-test",
            display_name="Aluno teste",
        )
        guardian_type = PersonType.objects.create(
            code="guardian-test",
            display_name="Responsável teste",
        )
        person = Person.objects.create(
            full_name="Maria Souza",
            cpf="123.456.789-00",
        )

        person.person_types.add(student_type, guardian_type)

        self.assertEqual(person.person_types.count(), 2)
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
                "holder_phone": "(62) 99999-1111",
                "holder_email": "carlos@example.com",
                "holder_password": "SenhaForte@123",
                "holder_password_confirm": "SenhaForte@123",
                "dependent_name": "João Dependente",
                "dependent_cpf": "12345678902",
                "dependent_birthdate": "02/02/2015",
                "dependent_password": "SenhaForte@456",
                "dependent_password_confirm": "SenhaForte@456",
                "dependent_kinship_type": "father",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        holder = created["holder"]
        dependent = created["dependent"]

        self.assertTrue(holder.person_types.filter(code="student").exists())
        self.assertTrue(holder.person_types.filter(code="guardian").exists())
        self.assertEqual(holder.access_account.person, holder)
        self.assertTrue(holder.access_account.check_password("SenhaForte@123"))
        self.assertTrue(dependent.person_types.filter(code="student").exists())
        self.assertTrue(dependent.person_types.filter(code="dependent").exists())
        self.assertEqual(dependent.access_account.person, dependent)
        self.assertTrue(dependent.access_account.check_password("SenhaForte@456"))
        self.assertTrue(
            PersonRelationship.objects.filter(
                source_person=holder,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
            ).exists()
        )
        self.assertEqual(User.objects.count(), 0)

    def test_guardian_registration_form_creates_guardian_and_student_accounts(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "guardian",
                "guardian_name": "Paula Responsável",
                "guardian_cpf": "98765432100",
                "guardian_phone": "(62) 99999-3333",
                "guardian_email": "paula@example.com",
                "guardian_password": "SenhaForte@789",
                "guardian_password_confirm": "SenhaForte@789",
                "student_name": "Pedro Aluno",
                "student_cpf": "98765432101",
                "student_birthdate": "03/03/2012",
                "student_password": "SenhaForte@987",
                "student_password_confirm": "SenhaForte@987",
                "student_kinship_type": "mother",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()

        guardian = created["guardian"]
        student = created["student"]

        self.assertTrue(guardian.person_types.filter(code="guardian").exists())
        self.assertTrue(student.person_types.filter(code="student").exists())
        self.assertTrue(student.person_types.filter(code="dependent").exists())
        self.assertTrue(guardian.access_account.check_password("SenhaForte@789"))
        self.assertTrue(student.access_account.check_password("SenhaForte@987"))

    def test_registration_form_requires_matching_password_confirmation(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Carlos Titular",
                "holder_cpf": "12345678901",
                "holder_birthdate": "01/01/1990",
                "holder_password": "SenhaForte@123",
                "holder_password_confirm": "SenhaForte@124",
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
        access_account.set_password("SenhaForte@123")
        access_account.save()

        reset_token = PortalPasswordResetToken.objects.create(access_account=access_account)

        self.assertTrue(reset_token.is_valid())
        self.assertGreater(reset_token.expires_at, timezone.now())

    def test_registration_derives_class_category_from_selected_group(self):
        seed_class_catalog()
        class_group = ClassGroup.objects.get(code="adult-lauro")
        class_schedule = class_group.schedules.order_by("display_order").first()

        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Aluno com Turma",
                "holder_cpf": "22345678901",
                "holder_birthdate": "01/01/1995",
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "holder_class_group": class_group.pk,
                "holder_class_schedule": class_schedule.pk,
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        created = form.save()
        holder = created["holder"]

        self.assertEqual(holder.class_group, class_group)
        self.assertEqual(holder.class_schedule, class_schedule)
        self.assertEqual(holder.class_category, class_group.class_category)

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
                "student_password": "123456",
                "student_password_confirm": "123456",
                "student_kinship_type": "mother",
                "extra_dependents_payload": json.dumps(
                    [
                        {
                            "full_name": "Dependente Extra 1",
                            "cpf": "32345678903",
                            "birth_date": "01/03/2015",
                            "password": "123456",
                            "password_confirm": "123456",
                            "kinship_type": "mother",
                        },
                        {
                            "full_name": "Dependente Extra 2",
                            "cpf": "32345678904",
                            "birth_date": "01/04/2016",
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

    def test_seed_person_matrix_creates_all_non_empty_type_combinations(self):
        result = seed_person_matrix()
        matrix_people = result["matrix_people"]

        self.assertEqual(len(matrix_people), 31)
        self.assertEqual(
            Person.objects.exclude(cpf="909.999.999-99").count(),
            31,
        )
        self.assertEqual(PortalAccount.objects.count(), 31)

        observed_combinations = {
            tuple(person.person_types.order_by("code").values_list("code", flat=True))
            for person in Person.objects.exclude(cpf="909.999.999-99")
        }
        self.assertEqual(len(observed_combinations), 31)

        dependent_people = Person.objects.filter(person_types__code="dependent").distinct()
        self.assertTrue(dependent_people.exists())
        for person in dependent_people:
            self.assertTrue(
                PersonRelationship.objects.filter(
                    target_person=person,
                    relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
                ).exists()
            )
