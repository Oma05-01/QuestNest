from django.contrib import admin
from .models import EventRule

@admin.register(EventRule)
class EventRuleAdmin(admin.ModelAdmin):
    list_display = ("event_type", "organisation", "action_type", "is_active", "execution_order")
    list_filter = ("event_type", "organisation", "action_type", "is_active")
    ordering = ("execution_order",)
