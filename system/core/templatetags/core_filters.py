import json

from django import template

register = template.Library()


@register.filter
def form_field(form, field_name):
    if form is None:
        return None
    return form[field_name] if field_name in form.fields else None


@register.filter
def attr(obj, attribute_name):
    if obj is None or not attribute_name:
        return None
    return getattr(obj, attribute_name, None)


@register.filter
def item(value, key):
    if value is None:
        return None
    try:
        return value.get(key)
    except AttributeError:
        return None


@register.filter
def json_attr(value):
    if not value:
        return ""
    return json.dumps(value, ensure_ascii=False)
