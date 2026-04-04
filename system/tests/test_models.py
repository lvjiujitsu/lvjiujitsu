from django.test import TestCase

from system.models import Person, PersonType


class PersonModelTestCase(TestCase):
    def test_person_can_have_multiple_types(self):
        student_type = PersonType.objects.create(
            code="student-test",
            display_name="Aluno teste",
        )
        guardian_type = PersonType.objects.create(
            code="guardian-test",
            display_name="Responsavel teste",
        )
        person = Person.objects.create(
            full_name="Maria Souza",
            cpf="123.456.789-00",
        )

        person.person_types.add(student_type, guardian_type)

        self.assertEqual(person.person_types.count(), 2)
        self.assertEqual(str(person), "Maria Souza")
