from django.contrib import admin
from .models import WorkspaceVerification, PropertyVerification, VerificationDocument

@admin.register(WorkspaceVerification)
class WorkspaceVerificationAdmin(admin.ModelAdmin):
    # 🟢 CHANGED: Replaced organisation with workspace
    list_display = ("workspace", "verified", "submitted_at", "verified_at", "reviewed_by")
    list_filter = ("verified", "workspace") # Added workspace filter for easier management
    search_fields = ("workspace__name", "reviewed_by__email") # Support searching by name/email
    raw_id_fields = ("workspace", "reviewed_by") # Cleaner for thousands of workspaces

@admin.register(PropertyVerification)
class PropertyVerificationAdmin(admin.ModelAdmin):
    # 🟢 CHANGED: Pulling the workspace name through the asset relationship
    # so admins can see who owns the property at a glance.
    list_display = ("asset", "get_workspace", "verified", "verified_at", "reviewed_by")
    list_filter = ("verified", "asset__workspace")
    filter_horizontal = ("documents",)
    raw_id_fields = ("asset", "reviewed_by")

    def get_workspace(self, obj):
        return obj.asset.workspace
    get_workspace.short_description = 'Workspace/Owner'