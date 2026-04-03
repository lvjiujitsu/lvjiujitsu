from decimal import Decimal

from django.db import models

from system.models.base import BaseModel


class DashboardDailySnapshot(BaseModel):
    snapshot_date = models.DateField(unique=True)
    active_students_count = models.PositiveIntegerField(default=0)
    pending_financial_students_count = models.PositiveIntegerField(default=0)
    paid_revenue_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    attendances_count = models.PositiveIntegerField(default=0)
    cancelled_subscriptions_count = models.PositiveIntegerField(default=0)
    active_pauses_count = models.PositiveIntegerField(default=0)
    overdue_invoices_count = models.PositiveIntegerField(default=0)
    under_review_proofs_count = models.PositiveIntegerField(default=0)
    requested_trial_classes_count = models.PositiveIntegerField(default=0)
    pending_checkout_requests_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-snapshot_date",)

    def __str__(self):
        return f"Snapshot {self.snapshot_date:%d/%m/%Y}"
