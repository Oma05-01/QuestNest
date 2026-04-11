import re
from django.apps import apps


def get_object_from_event(event):
    """
    Takes an Event model and returns the actual database instance it refers to.
    e.g., turns object_type="Escrow" and object_id="123" into the Escrow object.
    """
    if not event.object_type or not event.object_id:
        return None

    # Search through all installed Django models to find the matching one
    for model in apps.get_models():
        if model.__name__ == event.object_type:
            try:
                return model.objects.get(id=event.object_id)
            except (model.DoesNotExist, ValueError, TypeError):
                # 🟢 Added ValueError and TypeError to catch UUID vs Integer mismatches!
                return None

    return None


def format_dynamic_text(text_template, related_object):
    """
    Replaces {variables} in a string with actual properties from the Django model.
    e.g., "Review {status} Escrow" -> "Review funded Escrow"
    """
    if not text_template or "{" not in text_template:
        return text_template

    if not related_object:
        return text_template

    # Find all words wrapped in curly braces {like_this}
    placeholders = re.findall(r'\{(.*?)\}', text_template)

    formatted_text = text_template
    for placeholder in placeholders:
        # Try to get the attribute from the object (e.g., object.status)
        # If it doesn't exist, just leave the placeholder as is so it doesn't crash
        value = getattr(related_object, placeholder, f"{{{placeholder}}}")

        # Swap the placeholder with the real value
        formatted_text = formatted_text.replace(f"{{{placeholder}}}", str(value))

    return formatted_text