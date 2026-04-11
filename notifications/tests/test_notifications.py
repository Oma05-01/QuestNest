import pytest
from django.core import mail
from django.urls import reverse
from decimal import Decimal
from notifications.models import Notification
from operations.services.event_service import log_event
from operations.constants import EventType


@pytest.mark.django_db
class TestNotificationSystem:

    def test_payment_success_triggers_notification_and_email(self, organisation, funded_tenant):
        """
        Ensures that a SUCCESSful payment event:
        1. Creates a Notification record in the DB.
        2. Sends an email to the user.
        """
        from payments.models import Payment

        # 1. SETUP: Create a payment manually
        payment = Payment.objects.create(
            organisation=organisation,
            user=funded_tenant,
            amount=Decimal("25000.00"),
            reference="TEST-NOTIF-001",
            status="success"
        )

        # 2. ACT: Log the event that triggers the rule
        log_event(
            organisation=organisation,
            event_type=EventType.PAYMENT_SUCCESS,
            object_type="Payment",
            object_id=str(payment.id)
        )

        # 3. ASSERT: Check Database
        notification = Notification.objects.filter(user=funded_tenant).latest('created_at')
        assert notification.title == "Payment Successful!"
        assert "₦25000.00" in notification.message
        assert notification.notification_type == "success"

        # 4. ASSERT: Check Email Dispatch
        # mail.outbox is a list of all emails sent during the test
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert sent_email.subject == "Payment Successful!"
        assert sent_email.to == [funded_tenant.email]

    def test_notification_idempotency(self, funded_tenant, organisation):
        """
        Ensures the create_notification service doesn't spam duplicate records.
        """
        from notifications.services.notification_service import create_notification

        params = {
            "user": funded_tenant,
            "organisation": organisation,
            "title": "Duplicate Check",
            "message": "This should only exist once.",
            "metadata": {"test_id": 123}
        }

        # Create twice
        create_notification(**params)
        create_notification(**params)

        # Should only have one in the DB
        count = Notification.objects.filter(title="Duplicate Check").count()
        assert count == 1