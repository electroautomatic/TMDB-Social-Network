from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using the key.
    Example: {{ mydict|get_item:key_var }}
    """
    return dictionary.get(key, [])

@register.filter
@stringfilter
def replace(value, arg):
    """
    Replaces all instances of the first argument with the second in the given string.
    Example: {{ "Hello_World"|replace:"_"," " }}
    """
    args = arg.split(',')
    if len(args) != 2:
        return value
    return value.replace(args[0], args[1]) 