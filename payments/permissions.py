from django.core.exceptions import PermissionDenied

def require_admin(user):
    if not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("Admin access required.")
