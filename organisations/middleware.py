from django.shortcuts import redirect


class OrganisationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith('/admin/') or request.path.startswith('/api/token/'):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        if request.path.startswith('/api/token/') or request.path.startswith('/accounts/'):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        request.organisation = None

        if not request.user.is_authenticated:
            return self.get_response(request)

        # Only apply to operator routes
        if request.path.startswith("/organisation/") or request.path.startswith("/assets/"):

            org_id = request.session.get("active_org_id")

            if org_id:
                from .models import Organisation
                try:
                    request.organisation = Organisation.objects.get(id=org_id)
                except Organisation.DoesNotExist:
                    request.organisation = None

        return self.get_response(request)

