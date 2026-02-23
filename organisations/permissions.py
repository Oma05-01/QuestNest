from django.http import HttpResponseForbidden
from functools import wraps
from .models import Membership

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
