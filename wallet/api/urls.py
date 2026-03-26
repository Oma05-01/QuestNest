from django.urls import path
from .views import MyWalletView, MyWalletTransactionsView

app_name = 'wallet'

urlpatterns = [
    path('', MyWalletView.as_view(), name='my-wallet'),
    path('transactions/', MyWalletTransactionsView.as_view(), name='my-transactions'),
]