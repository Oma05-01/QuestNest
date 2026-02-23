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

        prop_id = request.GET.get('property_id') or request.POST.get('property_id')
        if prop_id:
            from properties.models import Property
            property_obj = Property.objects.filter(id=prop_id).first()
            if property_obj and not property_obj.is_verified:
                return HttpResponseForbidden("Property is not verified.")

        response = self.get_response(request)
        return response
