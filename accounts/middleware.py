from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    PUBLIC_PATHS = [
        '/api/token/',
        '/api/token/refresh/',
        '/accounts/enter-email/',
        '/accounts/enter-password/',
        '/accounts/register/',
        '/accounts/password-reset/',
        '/accounts/password-reset/done/',
        '/reset/',
        '/reset/done/',
        '/accounts/verify-email/',
        '/admin/',
        '/static/',
        '/media/',
    ]

    # Define role-based access for dashboards
    ROLE_DASHBOARD_PATHS = {
        'tenant': '/dashboard/tenant/',
        'landlord': '/dashboard/landlord/',
        'agent': '/dashboard/agent/',
        'admin': '/dashboard/admin/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path


        if path.startswith('/api/'):
            return self.get_response(request)


        # Allow public URLs
        if not any(path.startswith(p) for p in self.PUBLIC_PATHS):
            if not request.user.is_authenticated:
                return redirect('enter_email')

            # Role-based dashboard access
            for role, dashboard_path in self.ROLE_DASHBOARD_PATHS.items():
                if path.startswith(dashboard_path) and request.user.role != role:
                    # Redirect to correct dashboard
                    correct_path = self.ROLE_DASHBOARD_PATHS.get(request.user.role, '/')
                    return redirect(correct_path)

        response = self.get_response(request)
        return response
