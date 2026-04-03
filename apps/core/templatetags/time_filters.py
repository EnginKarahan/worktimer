from django import template

register = template.Library()


@register.filter
def hours_decimal(minutes):
    """Convert minutes to decimal hours with 2 decimal places."""
    if minutes is None:
        return "0.00"
    return f"{minutes / 60:.2f}"


@register.filter
def hours_time(minutes):
    """Convert minutes to H:MM format."""
    if minutes is None:
        return "0:00"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"
