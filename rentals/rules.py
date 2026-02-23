from operations.rules import register_rule
from operations.constants import EventType
from rentals.models import Tenancy
from properties.models import Property

@register_rule(trigger_event=EventType.ESCROW_RELEASED)
def activate_tenancy_on_escrow_release(event):
    """
    When an escrow is released, activate the corresponding tenancy.
    If the tenancy doesn't exist yet, create it.
    """
    escrow = event.object  # Escrow instance

    # Ensure we have property and tenant
    if not escrow.property or not escrow.tenant:
        return

    # Check if tenancy already exists for this property & tenant
    tenancy, created = Tenancy.objects.get_or_create(
        property=escrow.property,
        tenant=escrow.tenant,
        organisation=escrow.property.organisation,
        defaults={
            "start_date": escrow.created_at.date(),
            "end_date": None,  # Can be updated later
            "status": Tenancy.PENDING
        }
    )

    # Activate tenancy if not active
    if tenancy.status != Tenancy.ACTIVE:
        tenancy.activate(actor=escrow.landlord)

@register_rule(trigger_event=EventType.TENANCY_ACTIVATED)
def mark_property_occupied(event):
    """
    When a tenancy is activated, mark the linked property as OCCUPIED.
    """
    tenancy = event.object  # Tenancy instance

    property_obj = tenancy.property
    if property_obj.status != Property.OCCUPIED:
        # Use your LifecycleMixin transition method if you have it
        property_obj.transition_to(
            Property.OCCUPIED,
            actor=tenancy.tenant,  # or tenancy.organisation.owner
            event_type=EventType.PROPERTY_STATUS_CHANGED,
            metadata={"to": Property.OCCUPIED}
        )