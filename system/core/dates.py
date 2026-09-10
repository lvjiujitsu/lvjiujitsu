from datetime import date, datetime

from django import forms
from django.utils import timezone
from django.utils.formats import date_format


class NativeDateInput(forms.DateInput):
    input_type = "date"


PT_BR_DATE_INPUT_ATTRS = {
    "autocomplete": "off",
    "lang": "pt-BR",
    "title": "Selecione a data no calendário.",
    "data-mask": "date",
}

PT_BR_DATE_INPUT_FORMAT = "%Y-%m-%d"
PT_BR_DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]


def today_context():
    today = timezone.localdate()
    return {
        "today": today,
        "today_weekday": date_format(today, "l"),
        "today_date": date_format(today, "SHORT_DATE_FORMAT"),
        "today_iso": today.strftime(PT_BR_DATE_INPUT_FORMAT),
    }


def parse_flexible_date(value: str | None):
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    return None


def parse_filter_date_param(value: str | None) -> tuple[date | None, str]:
    normalized = (value or "").strip()
    if not normalized:
        return None, ""
    parsed = parse_flexible_date(normalized)
    if parsed is None:
        return None, normalized
    return parsed, parsed.strftime(PT_BR_DATE_INPUT_FORMAT)


def clean_pt_br_date_value(value):
    if value in (None, ""):
        return value
    if hasattr(value, "year"):
        return value
    parsed = parse_flexible_date(str(value))
    if parsed is None:
        raise forms.ValidationError("Data inválida. Use dd/mm/aaaa ou selecione no calendário.")
    return parsed


def apply_pt_br_date_field(form, field_name, *, extra_attrs=None):
    if field_name not in form.fields:
        return
    attrs = {**PT_BR_DATE_INPUT_ATTRS, **(extra_attrs or {})}
    existing_class = form.fields[field_name].widget.attrs.get("class")
    if existing_class:
        attrs["class"] = existing_class
    form.fields[field_name].widget = NativeDateInput(
        format=PT_BR_DATE_INPUT_FORMAT,
        attrs=attrs,
    )
    form.fields[field_name].input_formats = PT_BR_DATE_INPUT_FORMATS[:]
