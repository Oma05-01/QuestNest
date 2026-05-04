from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from operations.constants import EventType
from .models import Payment

# If a tenant pays via Bank Transfer to the landlord directly,
# and the landlord confirms it, the Admin can click a button in the dashboard to manually move the payment to SUCCESS.
@login_required
def mark_payment_success(request, pk):

    payment = get_object_or_404(
        Payment,
        pk=pk,
        organisation=request.organisation
    )

    payment.transition_to(
        Payment.SUCCESS,
        actor=request.user,
        event_type=EventType.PAYMENT_STATUS_CHANGED,
        metadata={
            "from": payment.status,
            "to": Payment.SUCCESS,
            "amount": str(payment.amount)
        }
    )

    return redirect("payment_list")
