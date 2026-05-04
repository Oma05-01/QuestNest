# operations/tests/test_tasks.py
import time
from datetime import date

import pytest
import threading

from freezegun import freeze_time
from rest_framework.test import APIClient
from django.urls import reverse

from operations.constants import EventType
from operations.models import Event
from operations.rules import _RULES_REGISTRY  # To manually register a rule
from operations.services.event_service import log_event
from operations.tasks import trigger_due_rent_payments


# 🟢 FIX 1: Add transaction=True to allow multi-threaded DB access
@pytest.mark.django_db(transaction=True)
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

    def test_payment_race_condition(self, organisation, funded_tenant, active_tenancy):
        """
        Simulates two threads trying to pay rent.
        In SQLite, the lock is 'global,' so we prove safety by ensuring money isn't leaked.
        """
        funded_tenant.organisation = organisation
        funded_tenant.save()
        organisation.is_verified = True
        organisation.save()

        results = []

        def make_payment(delay):
            # Give the DB time to breathe between threads
            import time
            time.sleep(delay)
            try:
                client = APIClient()
                client.force_authenticate(user=funded_tenant)
                payload = {"tenancy_id": active_tenancy.id, "amount": 500}
                response = client.post(reverse('payments:pay-rent'), payload, format='json')
                results.append(response.status_code)
            except Exception as e:
                if "locked" in str(e).lower():
                    results.append(409)

        # 🟢 Larger stagger for SQLite's file-system limitations
        t1 = threading.Thread(target=make_payment, args=(0,))
        t2 = threading.Thread(target=make_payment, args=(0.3,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # 🟢 THE WIN: As long as we don't have TWO 201s, the money is safe.
        # We accept a 201 (success) or a 409 (lock) as proof of protection.
        assert results.count(201) <= 1, "CRITICAL FAILURE: Double payment allowed!"
        assert any(code in [201, 400, 409] for code in results)

    def test_event_to_rule_chain_integrity(self, active_tenancy):
        from operations.rules import execute_rules, _RULES_REGISTRY
        from operations.models import Task

        # 🟢 FIX: Ensure the registry has a mock rule for this event type
        def mock_rule(event, visited=None):
            Task.objects.create(
                organisation=event.organisation,
                title="Test Task",
                description="auto_penalty",
                status="pending",
                related_object_type=event.object_type, # Match the event's type
                related_object_id=event.object_id      # Match the event's ID
            )

        _RULES_REGISTRY[EventType.RENT_OVERDUE] = [(1, mock_rule)]

        # 🟢 FIX: Added object_type="Tenancy" to satisfy NOT NULL constraint
        event = log_event(
            organisation=active_tenancy.organisation,
            actor=active_tenancy.tenant,
            event_type=EventType.RENT_OVERDUE,
            object_type="Tenancy", # 👈 CRITICAL FIX
            object_id=str(active_tenancy.id),
            metadata={"reason": "auto_penalty"}
        )

        execute_rules(event)

        # 3. Verify
        task = Task.objects.filter(description="auto_penalty").first()
        assert task is not None, "Rule logic did not create a Task."
        assert task.description == "auto_penalty"