from django.test import TestCase

from system.forms import PortalRegistrationForm
from system.models import BiologicalSex


class PortalRegistrationFormMartialArtTestCase(TestCase):
    def test_clears_martial_art_details_when_answer_is_no(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Aluno Sem Historico",
                "holder_cpf": "12345678915",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "holder_has_martial_art": "no",
                "holder_martial_art": "jiu_jitsu",
                "holder_martial_art_graduation": "Faixa cinza",
                "holder_jiu_jitsu_belt": "blue",
                "holder_jiu_jitsu_stripes": "2",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["holder_martial_art"], "")
        self.assertEqual(form.cleaned_data["holder_martial_art_graduation"], "")
        self.assertEqual(form.cleaned_data["holder_jiu_jitsu_belt"], "")
        self.assertIsNone(form.cleaned_data["holder_jiu_jitsu_stripes"])

    def test_requires_martial_art_when_answer_is_yes(self):
        form = PortalRegistrationForm(
            data={
                "registration_profile": "holder",
                "holder_name": "Aluno Com Historico",
                "holder_cpf": "12345678916",
                "holder_birthdate": "01/04/1995",
                "holder_biological_sex": BiologicalSex.MALE,
                "holder_password": "123456",
                "holder_password_confirm": "123456",
                "holder_has_martial_art": "yes",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("holder_martial_art", form.errors)
