from rest_framework import serializers
from wallet.models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):
    """
    Returns the balance and identity of a wallet.
    A wallet can belong to either a Workspace or a User.
    """
    # Balance is a @property on the model calculating total credits - total debits
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    # 🟢 ADDED: Identify the owner of this wallet
    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'workspace_id', 'owner_name', 'balance', 'created_at']

    def get_owner_name(self, obj):
        # Return the Business name if it's a workspace wallet,
        # otherwise return the human's name.
        if obj.workspace:
            return obj.workspace.name
        return obj.user.name if obj.user else "System"


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Detailed ledger entry for every kobo/cent moving in or out.
    """
    # 🟢 ADDED: Human-readable type (e.g., "Credit" or "Debit")
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )

    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'amount',
            'transaction_type',
            'transaction_type_display',
            'reference',
            'description',
            'created_at'
        ]