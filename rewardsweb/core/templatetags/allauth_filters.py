"""Module containing Django allauth's tags and filters."""

from django import template

register = template.Library()


@register.filter(name="add_input_classes")
def add_input_classes(field, css_classes):
    widget = field.field.widget

    existing_classes = widget.attrs.get("class", "")
    widget.attrs["class"] = f"{existing_classes} {css_classes}".strip()

    return field
