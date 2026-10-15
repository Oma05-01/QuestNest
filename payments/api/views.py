import hmac
import hashlib
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# 🟢 CHANGED: Imported our context-aware permission
from core.api.permissions import IsWorkspaceMember
from operations.constants import EventType
from questnest import settings
from .serializers import PayRentSerializer
from payments.models import Payment
from payments.services.paystack import PaystackService
from payments.services.payment_service import pay_rent


class InitializePaystackPaymentView(APIView):
    """
    POST /api/payments/paystack/initialize/
    Initializes a transaction with Paystack and returns a checkout URL.
    """
    # 🟢 CHANGED: Replaced rigid role checks with context validation
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request):
        tenancy_id = request.data.get('tenancy_id')
        amount = request.data.get('amount')
        user = request.user

        # 1. Generate unique reference
        reference = f"QN-{uuid.uuid4().hex[:10].upper()}"

        # 2. Create the internal record (Initiated state)
        payment = Payment.objects.create(
            user=user,
            workspace=request.workspace, # 🟢 CHANGED: Scoped to the active workspace header
            amount=amount,
            reference=reference,
            status=Payment.INITIATED,
            metadata={"tenancy_id": tenancy_id}
        )

        # 3. Get Paystack URL from the service layer
        paystack_data = PaystackService.initialize_payment(
            email=user.email,
            amount_naira=amount,
            reference=reference,
            metadata={
                "payment_id": str(payment.id),
                "workspace_id": str(request.workspace.id) # 🟢 ADDED: Great for external auditing
            }
        )

        if paystack_data.get('status'):
            return Response({
                "checkout_url": paystack_data['data']['authorization_url'],
                "reference": reference
            }, status=status.HTTP_200_OK)

        return Response({"error": "Paystack initialization failed"}, status=status.HTTP_400_BAD_REQUEST)


class PayRentView(APIView):
    """
    POST /api/payments/pay-rent/
    Handles internal wallet-to-wallet rent payments.
    """
    # 🟢 CHANGED: Replaced rigid role checks
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request):
        # 1. Validate incoming data (Serializer handles checking if Tenancy belongs to Workspace)
        serializer = PayRentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # 2. Execute business logic (Internal Wallet Transfer)
        payment = pay_rent(
            tenant=request.user,
            tenancy=serializer.validated_data['tenancy'],
            amount=serializer.validated_data['amount']
        )

        return Response(
            {
                "message": "Payment successful.",
                "payment_reference": payment.reference,
                "status": payment.status
            },
            status=status.HTTP_201_CREATED
        )


@csrf_exempt
def paystack_webhook(request):
    """
    Public endpoint for Paystack to send transaction status updates.
    """
    payload = request.body
    sig_header = request.headers.get('x-paystack-signature')

    if not sig_header:
        return HttpResponse(status=400)

    # 1. Security Check: Verify signature
    hash = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    if hash != sig_header:
        return HttpResponse(status=400)

    # 2. Process event
    event_data = json.loads(payload)
    event_type = event_data['event']
    data = event_data['data']
    reference = data.get('reference')

    try:
        payment = Payment.objects.get(reference=reference)

        # 🟢 CASE 1: CHARGE SUCCESS
        if event_type == 'charge.success':
            if payment.status != Payment.SUCCESS:
                # 🟢 Because we updated LifecycleMixin, this transition automatically
                # routes the event to `payment.workspace`!
                payment.transition_to(
                    Payment.SUCCESS,
                    actor=payment.user,
                    event_type=EventType.PAYMENT_SUCCESS,
                    metadata={
                        "gateway": "paystack",
                        "channel": data.get('channel'),
                        "ip_address": data.get('ip_address')
                    }
                )

        # 🔴 CASE 2: CHARGE FAILED
        elif event_type == 'charge.failed':
            if payment.status != Payment.FAILED:
                failure_reason = data.get('gateway_response', 'Transaction declined')
                payment.transition_to(
                    Payment.FAILED,
                    actor=payment.user,
                    event_type=EventType.PAYMENT_FAILED, # 🟢 MINOR FIX: Changed from PAYMENT_STATUS_CHANGED to PAYMENT_FAILED to match your rules.py listener
                    metadata={
                        "gateway": "paystack",
                        "failure_reason": failure_reason,
                        "status_to": "failed"
                    }
                )

    except Payment.DoesNotExist:
        # Log this if necessary, but return 200 so Paystack stops retrying
        pass

    return HttpResponse(status=200)