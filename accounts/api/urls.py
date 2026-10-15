from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CheckEmailView,
    LoginView,
    RegisterView,
    UserUpdateView,
    VerifyEmailView,
    ResendVerificationEmailView,
    LogoutView
)

app_name = 'accounts'

urlpatterns = [
    # --- Authentication (Identity Layer) ---
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Identity Verification ---
    path('check-email/', CheckEmailView.as_view(), name='check-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),

    # --- User Profile ---
    path('profile/', UserUpdateView.as_view(), name='profile-update'),
]