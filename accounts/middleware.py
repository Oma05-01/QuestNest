from django.shortcuts import redirect

class LoginRequiredMiddleware:
    # 🟢 Cleaned up to explicitly list open paths
    PUBLIC_PATHS = [
        '/api/',  # We bypass APIs here because Django Rest Framework handles API auth!
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

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 🟢 If the path is NOT public, enforce authentication
        if not any(path.startswith(p) for p in self.PUBLIC_PATHS):
            if not request.user.is_authenticated:
                return redirect('enter_email')

        # 🟢 REMOVED all the dashboard redirection logic.
        # The frontend will now determine what UI to show based on the active Workspace!

        response = self.get_response(request)
        return response