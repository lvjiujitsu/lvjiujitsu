from pathlib import Path
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from system.models import AuditLog, ExportRequest
from system.tests.factories import AdminUserFactory, EmergencyRecordFactory, MonthlyInvoiceFactory


def _make_workspace_tmp_dir():
    base_dir = Path(__file__).resolve().parents[3] / "test_artifacts" / uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


@pytest.mark.django_db
def test_admin_can_view_report_center(client):
    admin = AdminUserFactory()
    client.force_login(admin)

    response = client.get(reverse("system:report-center"))

    assert response.status_code == 200
    assert "Relatorios e auditoria" in response.content.decode()


@pytest.mark.django_db
def test_admin_can_export_audit_csv_from_report_center(client, settings):
    base_dir = _make_workspace_tmp_dir()
    control_file = base_dir / "critical.flag"
    control_file.write_text("EXPORT_ALLOWED=1", encoding="utf-8")
    settings.CRITICAL_EXPORT_CONTROL_FILE = str(control_file)
    settings.REPORT_EXPORTS_DIR = str(base_dir / "exports")
    admin = AdminUserFactory()
    AuditLog.objects.create(
        category=AuditLog.CATEGORY_SYSTEM,
        action="manual_seed",
        status=AuditLog.STATUS_SUCCESS,
        actor_user=admin,
    )
    client.force_login(admin)

    response = client.post(
        reverse("system:report-center"),
        data={
            "report_type": ExportRequest.TYPE_AUDIT,
            "start_date": timezone.localdate().isoformat(),
            "end_date": timezone.localdate().isoformat(),
            "filters-start_date": timezone.localdate().isoformat(),
            "filters-end_date": timezone.localdate().isoformat(),
        },
    )
    export_request = ExportRequest.objects.get(report_type=ExportRequest.TYPE_AUDIT)

    assert response.status_code == 302
    assert export_request.status == ExportRequest.STATUS_SUCCEEDED
    assert Path(export_request.file_path).exists()


@pytest.mark.django_db
def test_marking_invoice_paid_generates_audit_log(client):
    admin = AdminUserFactory()
    invoice = MonthlyInvoiceFactory()
    client.force_login(admin)

    response = client.post(reverse("system:invoice-mark-paid", kwargs={"uuid": invoice.uuid}))

    assert response.status_code == 302
    assert AuditLog.objects.filter(category=AuditLog.CATEGORY_FINANCE, action="invoice_paid").exists()


@pytest.mark.django_db
def test_emergency_quick_access_generates_audit_log(client):
    admin = AdminUserFactory()
    emergency_record = EmergencyRecordFactory()
    client.force_login(admin)

    response = client.get(
        reverse("system:emergency-quick-access"),
        data={"student": str(emergency_record.student.uuid)},
    )

    assert response.status_code == 200
    assert AuditLog.objects.filter(category=AuditLog.CATEGORY_EMERGENCY, action="emergency_record_viewed").exists()
