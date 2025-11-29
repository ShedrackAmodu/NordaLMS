from django import template
from django.apps import apps

register = template.Library()

@register.filter
def instanceof(obj, class_name):
    """Check if object is instance of given class name"""
    try:
        model_class = apps.get_model('quiz', class_name)
        return isinstance(obj, model_class)
    except (LookupError, ValueError):
        return False

@register.filter
def answer_choice_to_string(question, answer_id):
    """Convert answer choice ID to string"""
    if hasattr(question, 'answer_choice_to_string'):
        return question.answer_choice_to_string(answer_id)
    return str(answer_id)

@register.filter
def index(sequence, position):
    """Access list element by index"""
    try:
        return sequence[int(position)]
    except (IndexError, TypeError, ValueError):
        return ""

@register.filter
def get_item(dictionary, key):
    """Get dictionary value by key"""
    return dictionary.get(key, "")

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return int(value) // int(arg)
    except (ValueError, TypeError):
        return 0
