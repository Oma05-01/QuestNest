from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Payment
from .services.paystack import PaystackService
from operations.constants import EventType


@shared_task
def reconcile_pending_payments():
    """
    Finds 'stuck' payments and verifies them against Paystack API.
    """
    # 1. Find payments stuck in INITIATED for > 15 mins
    threshold = timezone.now() - timedelta(minutes=15)
    stuck_payments = Payment.objects.filter(
        status=Payment.INITIATED,
        created_at__lt=threshold
    )

    for payment in stuck_payments:
        # 2. Call Paystack Verify API
        response = PaystackService.verify_payment(payment.reference)

        if response.get('status') and response['data']['status'] == 'success':
            # 🟢 Found a missing success! Update and trigger rules.
            payment.transition_to(
                Payment.SUCCESS,
                actor=payment.user,
                event_type=EventType.PAYMENT_SUCCESS,
                metadata={"reason": "reconciliation_sync", "gateway": "paystack"}
            )

        elif response.get('status') and response['data']['status'] in ['failed', 'abandoned']:
            # 🔴 Transaction actually failed or user closed the tab
            payment.transition_to(
                Payment.FAILED,
                actor=payment.user,
                event_type=EventType.PAYMENT_STATUS_CHANGED,
                metadata={"reason": "reconciliation_sync", "failure_reason": "abandoned"}
            )