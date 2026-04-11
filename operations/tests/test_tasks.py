import pytest
from datetime import date
from freezegun import freeze_time
from django.utils import timezone
from operations.tasks import trigger_due_rent_payments
from operations.models import Event
from operations.constants import EventType


@pytest.mark.django_db
class TestMidnightScanTasks:

    def test_trigger_due_rent_payments_logic(self, organisation, funded_tenant, active_tenancy):
        organisation.is_verified = True
        organisation.save()

        # 🟢 Use a common setup for the tenancy
        active_tenancy.next_payment_date = date(2026, 4, 15)
        active_tenancy.grace_period_days = 5
        active_tenancy.late_fee_applied = False  # Ensure this is clean
        active_tenancy.save()

        # --- SCENARIO A: It's Due Day ---
        with freeze_time("2026-04-15"):
            trigger_due_rent_payments()
            assert Event.objects.filter(event_type=EventType.RENT_PAYMENT_DUE).exists()

        # 🟢 REFRESH THE STATE for Scenario C
        # We want to simulate a tenancy that MISSED its payment and stayed 'Active'
        active_tenancy.late_fee_applied = False
        active_tenancy.next_payment_date = date(2026, 4, 15)  # Keep it on the old date
        active_tenancy.save()

        # --- SCENARIO C: It's officially Overdue (April 21) ---
        with freeze_time("2026-04-21"):
            # Clear events so we only count the new one
            Event.objects.all().delete()

            trigger_due_rent_payments()

            overdue_exists = Event.objects.filter(
                event_type=EventType.RENT_OVERDUE,
                object_id=str(active_tenancy.id)
            ).exists()

            assert overdue_exists, "Should log RENT_OVERDUE when today > grace_limit"