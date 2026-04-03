from pathlib import Path
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from system.models import AuditLog, CsvExportControl, ExportRequest
from system.services.reports.exports import get_or_create_export_control, request_csv_export
from system.tests.factories import AdminUserFactory


def _make_workspace_tmp_dir():
    base_dir = Path(__file__).resolve().parents[3] / "test_artifacts" / uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


@pytest.mark.django_db
def test_export_control_is_created_from_settings(settings):
    settings.CRITICAL_EXPORT_CONTROL_FILE = "C:/tmp/critical_exports.flag"

    control = get_or_create_export_control()

    assert control.name == "critical_csv_exports"
    assert control.control_file_path == "C:/tmp/critical_exports.flag"


@pytest.mark.django_db
def test_csv_export_fails_when_control_file_is_missing(settings):
    base_dir = _make_workspace_tmp_dir()
    settings.CRITICAL_EXPORT_CONTROL_FILE = str(base_dir / "missing.flag")
    settings.REPORT_EXPORTS_DIR = str(base_dir / "exports")
    admin = AdminUserFactory()

    with pytest.raises(ValidationError, match="Arquivo de controle ausente"):
        request_csv_export(
            report_type=ExportRequest.TYPE_AUDIT,
            requested_by=admin,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )

    control = CsvExportControl.objects.get(name="critical_csv_exports")
    assert control.last_validation_status == CsvExportControl.STATUS_INVALID


@pytest.mark.django_db
def test_csv_export_fails_when_control_file_is_invalid(settings):
    base_dir = _make_workspace_tmp_dir()
    control_file = base_dir / "invalid.flag"
    control_file.write_text("EXPORT_ALLOWED=0", encoding="utf-8")
    settings.CRITICAL_EXPORT_CONTROL_FILE = str(control_file)
    settings.REPORT_EXPORTS_DIR = str(base_dir / "exports")
    admin = AdminUserFactory()

    with pytest.raises(ValidationError, match="Arquivo de controle invalido"):
        request_csv_export(
            report_type=ExportRequest.TYPE_AUDIT,
            requested_by=admin,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )


@pytest.mark.django_db
def test_csv_export_fails_when_control_file_is_blocked(settings, monkeypatch):
    base_dir = _make_workspace_tmp_dir()
    control_file = base_dir / "blocked.flag"
    control_file.write_text("EXPORT_ALLOWED=1", encoding="utf-8")
    settings.CRITICAL_EXPORT_CONTROL_FILE = str(control_file)
    settings.REPORT_EXPORTS_DIR = str(base_dir / "exports")
    admin = AdminUserFactory()

    def raise_blocked(_path):
        raise OSError("locked")

    monkeypatch.setattr("system.services.reports.exports._read_control_file", raise_blocked)

    with pytest.raises(ValidationError, match="Arquivo de controle bloqueado"):
        request_csv_export(
            report_type=ExportRequest.TYPE_AUDIT,
            requested_by=admin,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )


@pytest.mark.django_db
def test_csv_export_succeeds_and_writes_file(settings):
    base_dir = _make_workspace_tmp_dir()
    control_file = base_dir / "valid.flag"
    control_file.write_text("EXPORT_ALLOWED=1", encoding="utf-8")
    settings.CRITICAL_EXPORT_CONTROL_FILE = str(control_file)
    settings.REPORT_EXPORTS_DIR = str(base_dir / "exports")
    admin = AdminUserFactory()
    AuditLog.objects.create(
        category=AuditLog.CATEGORY_SYSTEM,
        action="seed_event",
        status=AuditLog.STATUS_SUCCESS,
        actor_user=admin,
    )

    export_request = request_csv_export(
        report_type=ExportRequest.TYPE_AUDIT,
        requested_by=admin,
        start_date=timezone.localdate(),
        end_date=timezone.localdate(),
    )

    exported_file = Path(export_request.file_path)
    assert export_request.status == ExportRequest.STATUS_SUCCEEDED
    assert exported_file.exists()
    assert "seed_event" in exported_file.read_text(encoding="utf-8")
