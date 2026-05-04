from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import EventRule, Event, RuleExecution


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

class RuleExecutionInline(admin.TabularInline):
    model = RuleExecution
    extra = 0
    readonly_fields = ['rule_name', 'colored_status', 'execution_time', 'error_message_preview', 'created_at']
    fields = ['rule_name', 'colored_status', 'execution_time', 'error_message_preview']
    can_delete = False

    @admin.display(description="Status")
    def colored_status(self, obj):
        colors = {
            'success': '#28a745',  # Green
            'failed': '#dc3545',   # Red
            'skipped': '#ffc107',  # Yellow
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, '#000'),
            obj.status.upper()
        )

    @admin.display(description="Error Preview")
    def error_message_preview(self, obj):
        if obj.error_message:
            return obj.error_message[:100] + "..." if len(obj.error_message) > 100 else obj.error_message
        return "-"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id_link', 'event_type', 'organisation', 'colored_status', 'object_link', 'created_at']
    list_filter = ['status', 'event_type', 'created_at']
    search_fields = ['id', 'object_id', 'organisation__name']
    readonly_fields = ['id', 'parent_event_link', 'metadata', 'created_at', 'updated_at']
    inlines = [RuleExecutionInline]

    @admin.display(description="Event ID")
    def id_link(self, obj):
        return str(obj.id)[:8] + "..."

    @admin.display(description="Status")
    def colored_status(self, obj):
        color = "#28a745" if obj.status == "processed" else "#dc3545" if obj.status == "failed" else "#6c757d"
        return format_html('<b style="color:{};">{}</b>', color, obj.status.upper())

    @admin.display(description="Related Object")
    def object_link(self, obj):
        if obj.object_id:
            return format_html('<code>{} ({})</code>', obj.object_type, obj.object_id[:8])
        return "-"

    @admin.display(description="Parent Event")
    def parent_event_link(self, obj):
        if obj.parent_event:
            url = reverse('admin:operations_event_change', args=[obj.parent_event.id])
            return format_html('<a href="{}">View Parent Event ({})</a>', url, str(obj.parent_event.id)[:8])
        return "Root Event"

@admin.register(RuleExecution)
class RuleExecutionAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'event', 'status', 'execution_time', 'created_at']
    list_filter = ['status', 'rule_name']
    search_fields = ['event__id', 'rule_name']