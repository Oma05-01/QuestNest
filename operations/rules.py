from operations.models import Task, RuleExecution
from operations.constants import EventType
from operations.services.event_service import log_event
from collections import defaultdict

def task_exists(organisation, title, related_object_type, related_object_id):
    return Task.objects.filter(
        organisation=organisation,
        title=title,
        related_object_type=related_object_type,
        related_object_id=str(related_object_id)
    ).exists()


def rule_already_executed(event, rule_name):
    return RuleExecution.objects.filter(
        event=event,
        rule_name=rule_name
    ).exists()


def mark_rule_executed(event, rule_name):
    RuleExecution.objects.create(
        event=event,
        rule_name=rule_name
    )

# ------------------------
# Rule Registry
# ------------------------
_RULES_REGISTRY = defaultdict(list)

def register_rule(trigger_event, priority=100):
    """
    Decorator to register a function as a rule for a specific event type.
    """
    def decorator(func):
        _RULES_REGISTRY[trigger_event].append((priority, func))
        return func
    return decorator

def execute_rules(event, visited=None):
    """
    Execute all rules registered for this event type.
    """
    # Simply trigger registered rules. No hard-coded logic here!
    if visited is None:
        visited = set()

        # Prevent circular execution
    if event.id in visited:
        return

    visited.add(event.id)

    rules = _RULES_REGISTRY.get(event.event_type, [])

    # Sort by priority (lower number runs first)
    sorted_rules = sorted(rules, key=lambda x: x[0])

    for _, rule in sorted_rules:

        rule_name = rule.__name__

        if rule_already_executed(event, rule_name):
            continue

        rule(event, visited=visited)

        mark_rule_executed(event, rule_name)

# ------------------------
# Registered Rules
# ------------------------

@register_rule(EventType.ASSET_STATUS_CHANGED)
def create_tenancy_agreement_task(event, visited=None):
    """Extracted from the hard-coded block"""
    if event.metadata.get("to") == "reserved":
        task = Task.objects.create(
            organisation=event.organisation,
            title="Prepare tenancy agreement",
            related_object_type=event.object_type, # Or Property, depending on your rename
            related_object_id=event.object_id,
            created_by=None
        )

        log_event(
            organisation=event.organisation,
            actor=None,
            event_type=EventType.TASK_CREATED,
            object_type="Task",
            object_id=str(task.id),
            metadata={"triggered_by_event": event.event_type},
            parent_event=event
        )

@register_rule(EventType.ESCROW_FUNDED) # Assuming this is your event type
def escrow_funded_reserve_unit(event, visited=None):
    # Fetch the actual object using the ID
    escrow = event.object
    unit = escrow.tenancy.unit

    if unit.status != unit.RESERVED:
        unit.transition_to(
            unit.RESERVED,
            actor=event.actor,
            event_type=EventType.UNIT_RESERVED,
        )

@register_rule(EventType.ESCROW_RELEASED) # Assuming this is your event type
def escrow_released_occupy_unit(event, visited=None):
    # Fetch the actual object using the ID
    escrow = event.object
    unit = escrow.tenancy.unit

    if unit.status != unit.OCCUPIED:
        unit.transition_to(
            unit.OCCUPIED,
            actor=event.actor,
            event_type=EventType.UNIT_OCCUPIED,
        )

@register_rule(EventType.ESCROW_FUNDED)
def activate_tenancy_on_payment(event, visited=None):
    escrow = event.object
    tenancy = escrow.tenancy

    if tenancy.status != tenancy.ACTIVE:
        tenancy.transition_to(
            tenancy.ACTIVE,
            actor=event.actor,
            event_type=EventType.TENANCY_ACTIVATED
        )

@register_rule(EventType.TENANCY_ACTIVATED, priority=10)
def mark_unit_occupied(event, visited=None):
    tenancy = event.object
    unit = tenancy.unit

    if unit.status != unit.OCCUPIED:
        unit.transition_to(
            unit.OCCUPIED,
            actor=event.actor,
            event_type=EventType.UNIT_OCCUPIED
        )

@register_rule(EventType.ESCROW_FUNDED)
def create_verification_task(event, visited=None):
    escrow = event.object

    task = Task.objects.create(
        organisation=escrow.organisation,
        title=f"Verify unit {escrow.unit.name} for move-in",
        related_object_type="Escrow",
        related_object_id=str(escrow.id),
        created_by=None
    )

    log_event(
        organisation=escrow.organisation,
        actor=None,
        event_type=EventType.TASK_CREATED,
        object_type="Task",
        object_id=str(task.id),
        metadata={"triggered_by_event": event.event_type},
        parent_event=event
    )


@register_rule(EventType.LEASE_SIGNED, priority=50)
def create_lease_move_in_preparation_task(event, visited=None):

    Task.objects.create(
        organisation=event.organisation,
        title="Prepare property for tenant move-in",
        related_object_type="Lease",
        related_object_id=str(event.object_id)
    )


@register_rule(EventType.LEASE_CREATED)
def auto_generate_lease_pdf(event, visited=None):

    from leases.models import LeaseAgreement
    from leases.services.lease_pdf_service import generate_lease_pdf

    lease = LeaseAgreement.objects.get(id=event.object_id)

    generate_lease_pdf(lease)


