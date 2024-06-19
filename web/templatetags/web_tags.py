import unicodedata
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active(context, *url_names):
    if context['request'].resolver_match.url_name in url_names:
        return "active"
    return ""

@register.filter(name='replace_spaces')
def replace_spaces(value):
    """Replace all spaces in the string with &nbsp;."""
    return value.replace(' ', '&nbsp;')

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def remove_diacritics(value):
    """
    Remove diacritics from a string.
    """
    normalized = unicodedata.normalize('NFD', value)
    without_diacritics = ''.join([c for c in normalized if unicodedata.category(c) != 'Mn'])
    return without_diacritics.lower()