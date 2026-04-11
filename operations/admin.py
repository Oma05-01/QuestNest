from django.contrib import admin
from .models import EventRule


@admin.register(EventRule)
class EventRuleAdmin(admin.ModelAdmin):
    # 🟢 1. Core Display
    list_display = (
        "event_type",
        "organisation",
        "action_type",
        "execution_order",
        "is_active"
    )

    # 🟢 2. Quick Filters (Moved is_active to the top for quick toggling)
    list_filter = (
        "is_active",
        "event_type",
        "action_type",
        "organisation"
    )

    # 🟢 3. Search Bar (Assuming organisation has a 'name' field)
    search_fields = (
        "event_type",
        "action_type",
        "organisation__name"
    )

    # 🟢 4. Inline Editing (Saves you from clicking into every record!)
    list_editable = (
        "execution_order",
        "is_active"
    )

    # 🟢 5. Default Sorting (Groups by org first, then execution order)
    ordering = (
        "organisation",
        "execution_order"
    )