from rest_framework import serializers
from wallet.models import Wallet, WalletTransaction

class WalletSerializer(serializers.ModelSerializer):
    # We explicitly declare balance so DRF knows to pull the @property
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'reference', 'description', 'created_at']