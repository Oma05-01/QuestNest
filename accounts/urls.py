from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('enter-email/', views.enter_email, name='enter_email'),
    path('enter-password/', views.enter_password, name='enter_password'),
    path('register/', views.register, name='register'),

    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),

    # Password reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]
