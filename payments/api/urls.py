from django.urls import path
from .views import (
    PayRentView,
    InitializePaystackPaymentView,
    paystack_webhook
)

app_name = 'payments'

urlpatterns = [
    # Internal Wallet Payment
    path('pay-rent/', PayRentView.as_view(), name='pay-rent'),

    # External Paystack Initialization
    path('paystack/initialize/', InitializePaystackPaymentView.as_view(), name='paystack-initialize'),

    # Paystack Webhook (This must be the exact URL you put in your Paystack Dashboard)
    path('paystack/webhook/', paystack_webhook, name='paystack-webhook'),
]