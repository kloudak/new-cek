from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active(context, *url_names):
    if context['request'].resolver_match.url_name in url_names:
        return "active"
    return ""