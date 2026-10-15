from django.urls import path
from .views import SubmitVerificationView

app_name = 'verification'

urlpatterns = [
    # 🟢 Simple, unified endpoint for all verification types
    path('submit/', SubmitVerificationView.as_view(), name='submit-verification'),
]