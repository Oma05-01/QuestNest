from django.shortcuts import redirect
from django.http import HttpResponseForbidden

class VerifiedEntityMiddleware:
    """
    Ensures only verified organisations/properties can perform sensitive actions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for tenants or public routes
        if getattr(request.user, "role", None) == "tenant":
            return self.get_response(request)

        # Example: block if organisation not verified
        if hasattr(request, "organisation"):
            if not getattr(request.organisation, "is_verified", False):
                return HttpResponseForbidden("Your organisation is not verified yet.")

        prop_id = request.GET.get('unit_id') or request.POST.get('unit_id')
        if prop_id:
            from assets.models import Unit
            unit_obj = Unit.objects.filter(id=prop_id).first()
            if unit_obj and not unit_obj.is_verified:
                return HttpResponseForbidden("Unit is not verified.")

        response = self.get_response(request)
        return response
