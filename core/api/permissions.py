from rest_framework.permissions import BasePermission


class IsTenant(BasePermission):
    """
    Allows access only to authenticated users who are tenants.
    """
    message = "You must be a registered tenant to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'tenant'
        )


class IsLandlord(BasePermission):
    """
    Allows access only to authenticated users who are landlords.
    """
    message = "You must be a registered landlord to access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'landlord'
        )


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