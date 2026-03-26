from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from wallet.models import Wallet
from .serializers import WalletSerializer, WalletTransactionSerializer

class MyWalletView(APIView):
    """ GET /api/wallet/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # get_or_create ensures we don't crash if a user somehow doesn't have a wallet yet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

class MyWalletTransactionsView(APIView):
    """ GET /api/wallet/transactions/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        # Fetch transactions ordered by newest first
        transactions = wallet.transactions.all().order_by('-created_at')
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)