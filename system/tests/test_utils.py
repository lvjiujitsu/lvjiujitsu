from django.test import TestCase

from system.utils.person_data import ensure_formatted_cpf


class EnsureFormattedCpfTests(TestCase):
    def test_valid_cpf_formats_correctly(self):
        self.assertEqual(ensure_formatted_cpf("52998224725"), "529.982.247-25")
        self.assertEqual(ensure_formatted_cpf("529.982.247-25"), "529.982.247-25")
        self.assertEqual(ensure_formatted_cpf("96001338914"), "960.013.389-14")
        self.assertEqual(ensure_formatted_cpf("10433218100"), "104.332.181-00")

    def test_invalid_check_digits_raises(self):
        with self.assertRaises(ValueError):
            ensure_formatted_cpf("038.348.557-60")

    def test_all_same_digits_raises(self):
        for digit in "0123456789":
            with self.assertRaises(ValueError):
                ensure_formatted_cpf(digit * 11)

    def test_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            ensure_formatted_cpf("1234567890")
        with self.assertRaises(ValueError):
            ensure_formatted_cpf("123456789012")

    def test_strips_formatting_before_validating(self):
        self.assertEqual(ensure_formatted_cpf("529982247  25"), "529.982.247-25")
