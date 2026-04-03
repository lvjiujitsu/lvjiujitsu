from django.utils import timezone

from system.models import DashboardDailySnapshot
from system.selectors.dashboard_selectors import build_admin_dashboard_metrics


def get_or_create_dashboard_daily_snapshot(*, reference_date=None):
    snapshot_date = reference_date or timezone.localdate()
    metrics = build_admin_dashboard_metrics(reference_date=snapshot_date)
    snapshot, created = DashboardDailySnapshot.objects.get_or_create(
        snapshot_date=snapshot_date,
        defaults=metrics,
    )
    if created:
        return snapshot
    changed_fields = []
    for field_name, value in metrics.items():
        if getattr(snapshot, field_name) == value:
            continue
        setattr(snapshot, field_name, value)
        changed_fields.append(field_name)
    if changed_fields:
        snapshot.save(update_fields=[*changed_fields, "updated_at"])
    return snapshot
