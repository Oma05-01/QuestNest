from django.urls import path
from .views import CheckEmailView, LoginView, RegisterView, UserUpdateView, VerifyEmailView

urlpatterns = [
    path('/', LoginView.as_view(), name='login'),
    path('check-email/', CheckEmailView.as_view(), name='check-email'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserUpdateView.as_view(), name='profile-update'),
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
]