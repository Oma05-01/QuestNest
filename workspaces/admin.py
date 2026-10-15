from django.contrib import admin
from .models import Workspace, Membership


class MembershipInline(admin.TabularInline):
    """
    Allows managing workspace memberships directly inside the Workspace detail view.
    """
    model = Membership
    extra = 1
    raw_id_fields = ('user',)
    fields = ('user', 'role', 'is_active')


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """
    The Command Center for Business Entities.
    """
    list_display = ('id', 'name', 'workspace_type', 'is_verified', 'created_at')
    list_filter = ('workspace_type', 'is_verified', 'created_at')
    search_fields = ('name', 'id')
    list_editable = ('is_verified',)
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')

    # 🟢 Embedded inline management
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """
    Direct Access to Workspace Access Rights & Bridge Records.
    """
    list_display = ('id', 'workspace', 'user', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'workspace__workspace_type')
    search_fields = ('user__email', 'user__name', 'workspace__name')
    list_editable = ('role', 'is_active')
    raw_id_fields = ('user', 'workspace')
    readonly_fields = ('id',)