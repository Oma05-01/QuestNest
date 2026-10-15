from rest_framework.permissions import BasePermission
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from functools import wraps


class IsSystemAdmin(BasePermission):
    """
    Allows access only to QuestNest system administrators.
    Replaces the old 'IsAdmin' to avoid confusion with Workspace Admins.
    """
    message = "QuestNest System administrator access required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsWorkspaceMember(BasePermission):
    """
    Base permission: Ensures the user provided a valid X-Workspace-ID header
    and is actually a member of that workspace.
    """
    message = "A valid Workspace ID is required in the headers (X-Workspace-ID)."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request, 'workspace', None))


class IsPersonalWorkspace(IsWorkspaceMember):
    """
    Replaces 'IsTenant'. Allows access if the active workspace is Personal.
    """
    message = "This action requires you to be operating in a Personal Workspace."

    def has_permission(self, request, view):
        # Must be a member, AND the workspace type must be personal
        has_base_perm = super().has_permission(request, view)
        return has_base_perm and request.workspace.workspace_type == 'personal'


class IsBusinessWorkspace(IsWorkspaceMember):
    """
    Replaces 'IsLandlord'. Allows access if the active workspace is Business.
    """
    message = "This action requires you to be operating in a Business Workspace."

    def has_permission(self, request, view):
        has_base_perm = super().has_permission(request, view)
        return has_base_perm and request.workspace.workspace_type == 'business'


class BelongsToWorkspace(permissions.BasePermission):
    """
    Ensures the user can only touch objects belonging to their currently active workspace.
    """
    message = "You do not have access to resources outside your active workspace."

    def has_permission(self, request, view):
        # 1. Ensure the user is logged in and has an active workspace
        if not request.user.is_authenticated or not getattr(request, 'workspace', None):
            return False

        # 2. 🟢 THE KYC FIX: Block 'Write' actions if the Workspace isn't verified
        if request.method not in permissions.SAFE_METHODS:
            if request.workspace.workspace_type == 'business' and not request.workspace.is_verified:
                self.message = "Transaction blocked. Your business workspace is not yet verified."
                return False

        return True

    def has_object_permission(self, request, view, obj):
        # 🛡️ This is the heart of Multi-Tenancy Object Security
        if hasattr(obj, 'workspace'):
            return obj.workspace == request.workspace

        return False


# =========================================================
# FUNCTION-BASED VIEW DECORATORS
# =========================================================

def require_system_admin(user):
    if not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("Admin access required.")


# Updated standard roles based on our new Membership model
ALLOWED_MANAGEMENT_ROLES = ["owner", "admin", "manager"]


def membership_required(view_func):
    """Decorator for FBVs to ensure a valid workspace context."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'workspace', None):
            return HttpResponseForbidden("Valid Workspace ID header required. You may not be a member.")
        return view_func(request, *args, **kwargs)

    return wrapper


def operator_required(view_func):
    """Decorator for FBVs to ensure the user is an owner, admin, or manager."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'workspace', None):
            return HttpResponseForbidden("Valid Workspace ID header required.")

        if request.workspace_role not in ALLOWED_MANAGEMENT_ROLES:
            return HttpResponseForbidden("Operator access required.")

        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(allowed_roles):
    """Dynamic decorator to restrict FBVs to specific workspace roles."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not getattr(request, 'workspace', None):
                return HttpResponseForbidden("Valid Workspace ID header required.")

            if request.workspace_role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission to perform this action.")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

def require_admin(user):
    """
    Service-layer validation to ensure a user has admin privileges.
    """
    if not user or not (user.is_staff or user.is_superuser):
        raise PermissionDenied("You do not have administrative privileges to perform this action.")