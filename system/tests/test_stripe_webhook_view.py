from unittest.mock import patch

import stripe
from django.test import TestCase
from django.urls import reverse


class StripeWebhookViewErrorLoggingTestCase(TestCase):
    def _post_event(self, event):
        with patch(
            "system.views.stripe_views.verify_webhook_event", return_value=event
        ):
            return self.client.post(
                reverse("system:stripe-webhook"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test-signature",
            )

    def test_processing_failure_returns_500_without_masking_exception(self):
        event = stripe.Event.construct_from(
            {"id": "evt_test_1", "type": "product.created", "data": {"object": {}}},
            "sk_test_dummy",
        )
        with patch(
            "system.views.stripe_views.process_stripe_event",
            side_effect=ValueError("boom"),
        ), self.assertLogs("system.views.stripe_views", level="ERROR") as logs:
            response = self._post_event(event)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("evt_test_1", logs.records[0].getMessage())
        self.assertIs(logs.records[0].exc_info[0], ValueError)
        self.assertEqual(str(logs.records[0].exc_info[1]), "boom")
