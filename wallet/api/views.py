import uuid

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from wallet.models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer
from payments.services.paystack import PaystackService

class MyWalletView(APIView):
    """ GET /api/wallet/ """
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Get My Wallet")
    def get(self, request):
        # 🟢 FIX: Separate Company Wallets from Personal Wallets
        if request.user.role == 'tenant':
            wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'organisation': None})
        else:
            wallet, _ = Wallet.objects.get_or_create(organisation=request.user.organisation, defaults={'user': None})

        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class MyWalletTransactionsView(APIView):
    """ GET /api/wallet/transactions/ """
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Get Wallet Transactions", responses=WalletTransactionSerializer(many=True))
    def get(self, request):
        # 🟢 FIX: Fetch the correct wallet based on role
        if request.user.role == 'tenant':
            wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'organisation': None})
        else:
            wallet, _ = Wallet.objects.get_or_create(organisation=request.user.organisation, defaults={'user': None})

        transactions = wallet.transactions.all().order_by('-created_at')
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class FundWalletInitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount_naira = request.data.get('amount')
        if not amount_naira or float(amount_naira) <= 0:
            return Response({"error": "Valid amount required"}, status=400)

        # Generate a unique reference for this specific wallet funding attempt
        reference = f"fund_{uuid.uuid4().hex[:12]}"

        # 🟢 Use your existing classmethods
        response = PaystackService.initialize_payment(
            email=request.user.email,
            amount_naira=float(amount_naira),
            reference=reference,
            metadata={"user_id": str(request.user.id), "type": "wallet_funding"}
        )

        if response.get('status'):
            return Response({
                "authorization_url": response['data']['authorization_url'],
                "reference": reference
            })

        return Response({"error": "Paystack initialization failed"}, status=502)


class FundWalletVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get('reference')

        if WalletTransaction.objects.filter(reference=reference).exists():
            return Response({"error": "Transaction already processed"}, status=400)

        # 🟢 Use your existing verification method
        response = PaystackService.verify_payment(reference)

        if response.get('status') and response['data']['status'] == 'success':
            amount_paid = response['data']['amount'] / 100.0

            with transaction.atomic():
                if request.user.role == 'tenant':
                    wallet, _ = Wallet.objects.get_or_create(user=request.user)
                else:
                    wallet, _ = Wallet.objects.get_or_create(organisation=request.user.organisation)

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount_paid,
                    transaction_type=WalletTransaction.CREDIT,
                    reference=reference,
                    description="Wallet Deposit via Paystack"
                )

            return Response({"message": "Wallet funded!"})

        return Response({"error": "Verification failed"}, status=400)