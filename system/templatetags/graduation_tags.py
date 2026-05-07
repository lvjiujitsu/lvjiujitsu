from django import template

register = template.Library()


@register.simple_tag
def belt_grade_slots(belt_rank, grade_number=0):
    if belt_rank is None:
        return []
    return belt_rank.get_grade_slots(grade_number or 0)
