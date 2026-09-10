import json
from system.business_rule.services.payroll_rules.constants import PayrollRuleError


def append_order_note_record(order, prefix, payload, *, save):
    line = prefix + json.dumps(payload, sort_keys=True)
    current_notes = (order.notes or "").strip()
    order.notes = "\n".join([item for item in (current_notes, line) if item])
    if save:
        order.save(update_fields=["notes", "updated_at"])
    return order


def read_order_note_records(notes, prefix):
    records = []
    for line in (notes or "").splitlines():
        if not line.startswith(prefix):
            continue
        raw_payload = line[len(prefix):]
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise PayrollRuleError("Registro de estorno inválido.") from exc
        if not isinstance(payload, dict):
            raise PayrollRuleError("Registro de estorno deve ser um objeto.")
        records.append(payload)
    return records
