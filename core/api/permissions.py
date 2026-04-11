from rest_framework.permissions import BasePermission
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from functools import wraps
from organisations.models import Membership

class IsTenant(BasePermission):
    """
    Allows access only to authenticated users who are tenants.
    """
    message = "You must be a registered tenant to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # 🟢 Allow the tenant OR an admin/staff to pass
        return user.role == 'tenant' or user.role == 'admin' or user.is_staff


class IsLandlord(BasePermission):
    """
    Allows access only to authenticated users who are landlords.
    """
    message = "You must be a registered landlord to access this resource."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # 🟢 Allow the landlord OR an admin/staff to pass
        return user.role == 'landlord' or user.role == 'admin' or user.is_staff


class IsAdmin(BasePermission):
    """
    Allows access only to system administrators.
    """
    message = "System administrator access required."

    def has_permission(self, request, view):
        # We check both the role AND Django's built-in is_staff flag
        # so superusers can always bypass this if needed.
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_staff)
        )


class IsLandlordOrAdmin(BasePermission):
    """
    Allows access to landlords OR administrators.
    """
    message = "You must be a landlord or administrator to perform this action."

    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False

        return request.user.role in ['landlord', 'admin'] or request.user.is_staff


class BelongsToOrganisation(permissions.BasePermission):
    """
    Ensures the user can only touch objects belonging to their organisation.
    """
    message = "You do not have access to resources outside your organisation."

    def has_permission(self, request, view):
        # 1. Ensure the user is logged in and has an organisation linked
        if not request.user.is_authenticated or not request.user.organisation:
            return False

        # 🟢 THE KYC FIX: Block 'Write' actions if the Org isn't verified
        # We allow 'SAFE_METHODS' (GET, HEAD, OPTIONS) so they can see their dashboard
        # but we block POST, PUT, DELETE (Transactions)
        if request.method not in permissions.SAFE_METHODS:
            if not request.user.organisation.is_verified:
                self.message = "Transaction blocked. Your organisation is not yet verified."
                return False

        return True

    def has_object_permission(self, request, view, obj):
        # 🛡️ This is the heart of Multi-Tenancy
        # obj is the model instance (Wallet, Payment, Tenancy, etc.)
        if hasattr(obj, 'organisation'):
            return obj.organisation == request.user.organisation

        # If the object is a User, check their organisation directly
        if hasattr(obj, 'user'):
            return obj.user.organisation == request.user.organisation

        from django.contrib.auth import get_user_model
        User = get_user_model()
        if isinstance(obj, User):
            return obj.organisation == request.user.organisation

        return False



def require_admin(user):
    if not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("Admin access required.")

allowed_roles_ini = ["owner", "manager", "operator"]

def membership_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.organisation:
            return HttpResponseForbidden("No active organisation.")

        membership = Membership.objects.filter(
            user=request.user,
            organisation=request.organisation
        ).first()

        if not membership:
            return HttpResponseForbidden("You are not a member of this organisation.")

        request.membership = membership
        return view_func(request, *args, **kwargs)

    return wrapper


def operator_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        membership = getattr(request, "membership", None)
        if not membership:
            return HttpResponseForbidden("Membership required.")

        if membership.role not in allowed_roles_ini:
            return HttpResponseForbidden("Operator access required.")

        return view_func(request, *args, **kwargs)

    return wrapper


def roles_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        membership = getattr(request, "membership", None)
        if not membership:
            return HttpResponseForbidden("Membership required.")

        if membership.role not in allowed_roles_ini:
            return HttpResponseForbidden("You do not have permission.")

        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            membership = getattr(request, "membership", None)
            if not membership:
                return HttpResponseForbidden("Membership required.")

            if membership.role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission.")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
