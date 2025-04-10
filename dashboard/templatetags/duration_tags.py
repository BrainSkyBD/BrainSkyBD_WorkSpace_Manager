# dashboard/templatetags/duration_tags.py
from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def duration_format(td):
    if not td:
        return "-"
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

@register.filter
def sum_time(project_times):
    total = timedelta()
    for project, time in project_times:
        total += time
    return total