from operations.rules import register_rule
from operations.constants import EventType
# 🟢 CHANGED: Import the service we refactored instead of the raw model
from operations.services.task_service import create_task

# 🟢 CHANGED: Listen directly to PAYMENT_SUCCESS and match the new decorator syntax
@register_rule(EventType.PAYMENT_SUCCESS, priority=50)
def create_task_on_successful_payment(event, visited=None):

    workspace = event.workspace # 🟢 CHANGED: Replaced organisation

    # 🟢 CHANGED: The task service now handles both DB creation AND event logging automatically!
    create_task(
        workspace=workspace,
        title="Confirm receipt of payment",
        related_object_type="Payment",
        related_object_id=event.object_id,
        parent_event=event, # Links the event genealogy for the Audit Trace
        actor=None # System generated
    )