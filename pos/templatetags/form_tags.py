from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divides the value by the arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Adds the arg to the value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def get_total(items, field):
    """Calculates total of a field in a list of items"""
    try:
        total = sum(getattr(item, field) or 0 for item in items)
        return total
    except (AttributeError, TypeError):
        return 0

@register.filter
def currency(value):
    """Formats a number as currency"""
    try:
        return "Ksh {:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "Ksh 0.00"
