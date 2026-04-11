from django.shortcuts import redirect
from django.http import HttpResponseForbidden

class VerifiedEntityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. THE MASTER KEY: Works for Admin / Session logins
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # 2. THE SAFE PASSAGE: Don't block login or auth routes.
        if request.path.startswith('/api/token/') or request.path.startswith('/accounts/'):
            return self.get_response(request)

        # 3. Skip middleware for tenants
        if getattr(request.user, "role", None) == "tenant":
            return self.get_response(request)

        # 4. THE REAL CHECK: Only block if an organisation actually exists and is unverified
        if hasattr(request, "organisation") and request.organisation is not None:
            if not getattr(request.organisation, "is_verified", False):
                return HttpResponseForbidden("Your organisation is not verified yet.")

        # 5. Unit verification check
        prop_id = request.GET.get('unit_id') or request.POST.get('unit_id')
        if prop_id:
            from assets.models import Unit
            unit_obj = Unit.objects.filter(id=prop_id).first()
            if unit_obj and not unit_obj.is_verified:
                return HttpResponseForbidden("Unit is not verified.")

        return self.get_response(request)