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
        template = (root / "templates" / "login" / "register.html").read_text(encoding="utf-8")
        script = (root / "static" / "system" / "js" / "auth" / "register.js").read_text(encoding="utf-8")

        self.assertNotIn("SENTINEL_TEST_XZ99", template)
        self.assertIn("register.js' %}?v=42", template)
        self.assertIn("function showOnlyWizardStep", script)
        self.assertIn("function rehydratePendingWizardState", script)
        self.assertIn("document.querySelectorAll('.wizard-step')", script)

    def test_user_data_render_functions_use_safe_dom_not_innerhtml(self):
        root = Path(__file__).resolve().parents[2]
        script = (root / "static" / "system" / "js" / "auth" / "register.js").read_text(encoding="utf-8")

        def function_body(name):
            start = script.index("function " + name)
            depth = 0
            started = False
            for idx in range(start, len(script)):
                ch = script[idx]
                if ch == "{":
                    depth += 1
                    started = True
                elif ch == "}":
                    depth -= 1
                    if started and depth == 0:
                        return script[start:idx + 1]
            raise AssertionError("function body not closed: " + name)

        review_body = function_body("renderReview")
        confirm_body = function_body("renderConfirmationSummary")

        self.assertNotIn(".innerHTML", review_body)
        self.assertNotIn(".innerHTML", confirm_body)
        self.assertIn("el(", review_body)
        self.assertIn("el(", confirm_body)


class CalendarTemplateStaticContractTestCase(SimpleTestCase):
    def test_calendar_template_loads_external_script_without_inline_logic(self):
        root = Path(__file__).resolve().parents[2]
        template = (root / "templates" / "calendar" / "calendar.html").read_text(encoding="utf-8")
        script = (root / "static" / "system" / "js" / "calendar" / "calendar.js").read_text(encoding="utf-8")

        self.assertIn("system/js/calendar/calendar.js' %}?v=1", template)
        self.assertNotIn("function applyTheme", template)
        self.assertNotIn("js-open-day-detail", template.split("<!-- ─── Scripts", 1)[-1])
        self.assertNotIn(".innerHTML", script)
        self.assertIn("function clearChildren", script)


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
