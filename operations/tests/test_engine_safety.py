import pytest
from operations.models import Event
from operations.services.event_service import log_event
from operations.rules import _RULES_REGISTRY, execute_rules


@pytest.mark.django_db
def test_engine_prevents_infinite_recursion(active_tenancy):
    LOOP_EVENT = "LOOP_TRIGGERED"

    # 1. Manually register the rule to be 100% sure the engine sees it
    def malicious_loop_rule(event, visited=None):
        log_event(
            organisation=event.organisation,
            event_type=LOOP_EVENT,
            object_type=event.object_type,
            object_id=event.object_id,
            parent_event=event
        )

    # Force it into the registry for this test
    _RULES_REGISTRY[LOOP_EVENT] = [(1, malicious_loop_rule)]

    try:
        # 2. Trigger the initial event
        initial_event = log_event(
            organisation=active_tenancy.organisation,
            event_type=LOOP_EVENT,
            object_type="Tenancy",
            object_id=str(active_tenancy.id)
        )

        # 3. Debugging: How many events were actually made?
        total_events = Event.objects.filter(event_type=LOOP_EVENT).count()
        print(f"\nDEBUG: Total events created: {total_events}")

        # 4. Assertions
        # The chain should have stopped at depth 10 (Total 11 events)
        assert total_events > 1, "The loop never started! The rule didn't fire."
        assert total_events <= 11, "The circuit breaker failed to stop the loop!"

        # The last event in the chain should be the one that failed the depth check
        last_event = Event.objects.filter(event_type=LOOP_EVENT).latest('created_at')
        assert last_event.status == "failed"
        assert "Infinite recursion" in last_event.metadata.get("error_loop", "")

    finally:
        # Clean up the registry so it doesn't affect other tests
        if LOOP_EVENT in _RULES_REGISTRY:
            del _RULES_REGISTRY[LOOP_EVENT]