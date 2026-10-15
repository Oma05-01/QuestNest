import uuid
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from core.api.permissions import IsWorkspaceMember
from wallet.models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer
from payments.services.paystack import PaystackService

def get_wallet_for_request(request):
    """
    Helper to fetch the wallet associated with the active workspace context.
    All wallets (both Personal and Business) link directly to request.workspace.
    """
    wallet, _ = Wallet.objects.get_or_create(
        workspace=request.workspace
    )
    return wallet

class MyWalletView(APIView):
    """ GET /api/wallet/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(summary="Get Active Wallet Balance")
    def get(self, request):
        wallet = get_wallet_for_request(request)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class MyWalletTransactionsView(APIView):
    """ GET /api/wallet/transactions/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(summary="Get Wallet Transaction Ledger", responses=WalletTransactionSerializer(many=True))
    def get(self, request):
        wallet = get_wallet_for_request(request)
        transactions = wallet.transactions.all().order_by('-created_at')
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class FundWalletInitView(APIView):
    """ POST /api/wallet/fund/init/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request):
        amount_naira = request.data.get('amount')
        if not amount_naira or float(amount_naira) <= 0:
            return Response({"error": "Valid amount required"}, status=status.HTTP_400_BAD_REQUEST)

        reference = f"fund_{uuid.uuid4().hex[:12]}"

        metadata = {
            "user_id": str(request.user.id),
            "workspace_id": str(request.workspace.id),
            "workspace_type": request.workspace.workspace_type,
            "type": "wallet_funding"
        }

        response = PaystackService.initialize_payment(
            email=request.user.email,
            amount_naira=float(amount_naira),
            reference=reference,
            metadata=metadata
        )

        if response.get('status'):
            return Response({
                "authorization_url": response['data']['authorization_url'],
                "reference": reference
            })

        return Response({"error": "Paystack initialization failed"}, status=status.HTTP_502_BAD_GATEWAY)


class FundWalletVerifyView(APIView):
    """ POST /api/wallet/fund/verify/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request):
        reference = request.data.get('reference')

        if WalletTransaction.objects.filter(reference=reference).exists():
            return Response({"error": "Transaction already processed"}, status=status.HTTP_400_BAD_REQUEST)

        response = PaystackService.verify_payment(reference)

        if response.get('status') and response['data']['status'] == 'success':
            amount_paid = response['data']['amount'] / 100.0

            with transaction.atomic():
                wallet = get_wallet_for_request(request)

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount_paid,
                    transaction_type=WalletTransaction.CREDIT,
                    reference=reference,
                    description=f"Wallet Deposit via Paystack ({request.workspace.workspace_type} context)"
                )

            return Response({"message": f"Successfully funded {request.workspace.name} wallet!"})

        return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)