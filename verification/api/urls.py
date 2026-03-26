from django.urls import path
from .views import SubmitVerificationView

app_name = 'verification'

urlpatterns = [
    path('submit/', SubmitVerificationView.as_view(), name='verification-submit'),
]