import csv
import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from system.models import AuditLog, CsvExportControl, ExportRequest
from system.selectors.report_selectors import (
    build_attendance_report_rows,
    build_audit_report_rows,
    build_finance_report_rows,
    build_graduation_report_rows,
)
from system.services.reports.audit import record_audit_log

logger = logging.getLogger(__name__)


def get_or_create_export_control():
    control, _ = CsvExportControl.objects.get_or_create(
        name="critical_csv_exports",
        defaults={"control_file_path": str(settings.CRITICAL_EXPORT_CONTROL_FILE)},
    )
    configured_path = str(settings.CRITICAL_EXPORT_CONTROL_FILE)
    if control.control_file_path != configured_path:
        control.control_file_path = configured_path
        control.save(update_fields=["control_file_path", "updated_at"])
    return control


def request_csv_export(*, report_type, requested_by, start_date, end_date):
    export_request = ExportRequest.objects.create(
        requested_by=requested_by,
        report_type=report_type,
        filters={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
    )
    try:
        control = get_or_create_export_control()
        _validate_export_control(control)
        rows = _build_report_rows(report_type=report_type, start_date=start_date, end_date=end_date)
        file_path = _write_csv_file(report_type=report_type, export_request=export_request, rows=rows)
        export_request.status = ExportRequest.STATUS_SUCCEEDED
        export_request.file_path = str(file_path)
        export_request.file_name = file_path.name
        export_request.row_count = len(rows)
        export_request.finished_at = timezone.now()
        export_request.error_message = ""
        export_request.save(
            update_fields=["status", "file_path", "file_name", "row_count", "finished_at", "error_message", "updated_at"]
        )
        record_audit_log(
            category=AuditLog.CATEGORY_REPORTS,
            action="csv_export_requested",
            actor_user=requested_by,
            target=export_request,
            metadata={"report_type": report_type, "row_count": len(rows)},
        )
        logger.info("csv_export_succeeded", extra={"report_type": report_type, "row_count": len(rows), "request_uuid": str(export_request.uuid)})
        return export_request
    except ValidationError as exc:
        export_request.status = ExportRequest.STATUS_FAILED
        export_request.finished_at = timezone.now()
        export_request.error_message = str(exc)
        export_request.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
        record_audit_log(
            category=AuditLog.CATEGORY_REPORTS,
            action="csv_export_failed",
            actor_user=requested_by,
            target=export_request,
            status=AuditLog.STATUS_FAILURE,
            metadata={"report_type": report_type, "error": str(exc)},
        )
        logger.warning("csv_export_failed", extra={"report_type": report_type, "request_uuid": str(export_request.uuid), "error": str(exc)})
        raise
    except Exception as exc:
        export_request.status = ExportRequest.STATUS_FAILED
        export_request.finished_at = timezone.now()
        export_request.error_message = str(exc)
        export_request.save(update_fields=["status", "finished_at", "error_message", "updated_at"])
        record_audit_log(
            category=AuditLog.CATEGORY_REPORTS,
            action="csv_export_failed",
            actor_user=requested_by,
            target=export_request,
            status=AuditLog.STATUS_FAILURE,
            metadata={"report_type": report_type, "error": str(exc)},
        )
        logger.exception("csv_export_failed_unexpected", extra={"report_type": report_type, "request_uuid": str(export_request.uuid)})
        raise


def _validate_export_control(control):
    path = Path(control.control_file_path)
    if not path.exists():
        return _invalidate_control(control, CsvExportControl.STATUS_INVALID, "Arquivo de controle ausente.")
    try:
        content = _read_control_file(path)
    except OSError as exc:
        return _invalidate_control(control, CsvExportControl.STATUS_ERROR, f"Arquivo de controle bloqueado: {exc}")
    if "EXPORT_ALLOWED=1" not in content:
        return _invalidate_control(control, CsvExportControl.STATUS_INVALID, "Arquivo de controle invalido.")
    _mark_control_valid(control)


def _read_control_file(path):
    with path.open("r+", encoding="utf-8") as handle:
        return handle.read()


def _invalidate_control(control, status, message):
    control.last_validated_at = timezone.now()
    control.last_validation_status = status
    control.last_validation_message = message
    control.save(update_fields=["last_validated_at", "last_validation_status", "last_validation_message", "updated_at"])
    raise ValidationError(message)


def _mark_control_valid(control):
    control.last_validated_at = timezone.now()
    control.last_validation_status = CsvExportControl.STATUS_VALID
    control.last_validation_message = "Arquivo de controle validado."
    control.save(update_fields=["last_validated_at", "last_validation_status", "last_validation_message", "updated_at"])


def _build_report_rows(*, report_type, start_date, end_date):
    builders = {
        ExportRequest.TYPE_ATTENDANCE: build_attendance_report_rows,
        ExportRequest.TYPE_FINANCE: build_finance_report_rows,
        ExportRequest.TYPE_GRADUATION: build_graduation_report_rows,
        ExportRequest.TYPE_AUDIT: build_audit_report_rows,
    }
    builder = builders[report_type]
    return builder(start_date=start_date, end_date=end_date)


def _write_csv_file(*, report_type, export_request, rows):
    exports_dir = Path(settings.REPORT_EXPORTS_DIR) / timezone.now().strftime("%Y") / timezone.now().strftime("%m")
    exports_dir.mkdir(parents=True, exist_ok=True)
    file_path = exports_dir / f"{report_type.lower()}-{export_request.uuid}.csv"
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
        else:
            writer.writerow({"empty": "Sem dados para o periodo selecionado."})
    return file_path
