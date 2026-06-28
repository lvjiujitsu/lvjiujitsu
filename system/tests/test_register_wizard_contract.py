import json
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from system.models import CategoryAudience, ClassCategory, ClassGroup, PreRegistration
from system.services.class_overview import build_class_group_filter_value
from system.views.auth_views import PortalRegisterView


class RegisterWizardStaticContractTestCase(SimpleTestCase):
    def test_register_template_and_script_contract(self):
        root = Path(__file__).resolve().parents[2]
        template = (root / "templates" / "login" / "register.html").read_text()
        script = (root / "static" / "system" / "js" / "auth" / "register.js").read_text()

        self.assertNotIn("SENTINEL_TEST_XZ99", template)
        self.assertIn("register.js' %}?v=36", template)
        self.assertIn("function showOnlyWizardStep", script)
        self.assertIn("function rehydratePendingWizardState", script)
        self.assertIn("document.querySelectorAll('.wizard-step')", script)


class PendingRegistrationSummaryContractTestCase(TestCase):
    def test_pending_summary_includes_training_person_class_group_ids(self):
        category = ClassCategory.objects.create(
            code="adult",
            display_name="Adulto",
            audience=CategoryAudience.ADULT,
        )
        holder_group = ClassGroup.objects.create(
            display_name="Adulto Manhã",
            class_category=category,
        )
        dependent_group = ClassGroup.objects.create(
            display_name="Adulto Noite",
            class_category=category,
        )
        holder_group_value = build_class_group_filter_value(
            holder_group.class_category_id,
            holder_group.display_name,
        )
        dependent_group_value = build_class_group_filter_value(
            dependent_group.class_category_id,
            dependent_group.display_name,
        )
        pre_registration = PreRegistration.objects.create(
            registration_profile="holder",
            holder_cpf="111.111.111-11",
            holder_email="aluno@example.com",
            form_snapshot={
                "registration_profile": "holder",
                "holder_name": "Aluno Titular",
                "holder_email": "aluno@example.com",
                "holder_phone": "(11) 99999-0000",
                "holder_class_groups": [holder_group_value],
                "dependent_name": "Dependente Um",
                "dependent_class_groups": [dependent_group_value],
                "extra_dependents_payload": json.dumps(
                    [
                        {
                            "full_name": "Dependente Dois",
                            "class_groups": [dependent_group_value],
                        }
                    ]
                ),
            },
        )
        view = PortalRegisterView()
        view.request = SimpleNamespace(
            session={"pending_pre_registration_id": pre_registration.pk}
        )

        summary = view._get_pending_person_summary()

        self.assertEqual(summary["person_type_code"], "student")
        self.assertEqual(summary["class_group_ids"], [holder_group_value])
        self.assertEqual(summary["students"][0]["class_group_ids"], [dependent_group_value])
        self.assertEqual(summary["students"][1]["class_group_ids"], [dependent_group_value])
