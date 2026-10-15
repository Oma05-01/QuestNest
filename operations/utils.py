import re
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist


def get_object_from_event(event):
    """
    Resolves the actual DB instance referenced by an Event.
    🛡️ Includes Workspace-Safety check to ensure tenant isolation.
    """
    if not event.object_type or not event.object_id:
        return None

    target_model = None
    # 🟢 OPTIMIZATION: Quick lookup for the model class
    for model in apps.get_models():
        if model.__name__ == event.object_type:
            target_model = model
            break

    if not target_model:
        return None

    try:
        obj = target_model.objects.get(id=event.object_id)

        # 🟢 NEW: Workspace-Safety Failsafe
        # If the object has a workspace attribute, it MUST match the event's workspace.
        if hasattr(obj, 'workspace') and event.workspace:
            if obj.workspace != event.workspace:
                return None  # Isolation breach prevented

        return obj
    except (target_model.DoesNotExist, ValueError, TypeError):
        return None


def format_dynamic_text(text_template, related_object):
    """
    Upgraded Formatter: Supports nested attributes like {unit.name}
    or {tenant.email} using dot notation.
    """
    if not text_template or "{" not in text_template:
        return text_template

    if not related_object:
        return text_template

    # Match anything inside curly braces: {property} or {property.sub_property}
    placeholders = re.findall(r'\{(.*?)\}', text_template)

    formatted_text = text_template
    for placeholder in placeholders:
        try:
            # 🟢 NEW: Support for nested dot-notation (e.g., 'unit.name')
            bits = placeholder.split('.')
            value = related_object
            for bit in bits:
                value = getattr(value, bit)

            formatted_text = formatted_text.replace(f"{{{placeholder}}}", str(value))
        except (AttributeError, ObjectDoesNotExist, TypeError):
            # If the path is invalid, we just keep the placeholder text
            continue

    return formatted_text