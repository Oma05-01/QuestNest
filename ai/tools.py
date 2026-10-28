# ai/tools.py
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from datetime import timedelta
from django.utils.timezone import now

# 1. Define strict schemas for every tool to enforce the workspace boundary
class WorkspaceInput(BaseModel):
    workspace_id: str = Field(
        description="The ID of the active workspace. This is injected by the system, do not ask the user for it."
    )

class ExpiryInput(WorkspaceInput):
    days_out: int = Field(default=90, description="Number of days from today to check for expiring leases.")

class UnitInput(WorkspaceInput):
    unit_name: Optional[str] = Field(default=None, description="Specific unit name to look up, e.g., 'Unit 101'.")

# 2. Use the @tool decorator to expose this to the LLM
@tool("get_vacant_units", args_schema=WorkspaceInput)
def get_vacant_units(workspace_id: str) -> str:
    """Retrieves a list of all currently vacant units across the property manager's portfolio."""
    from assets.models import Unit
    from rentals.models import Tenancy

    # Identify units currently occupied
    active_unit_ids = Tenancy.objects.filter(
        workspace_id=workspace_id,
        status='ACTIVE'  # Ensure this matches your Tenancy.ACTIVE constant
    ).values_list('unit_id', flat=True)

    # Filter for units NOT in the active list
    vacant_units = Unit.objects.filter(
        asset__workspace_id=workspace_id
    ).exclude(id__in=active_unit_ids)

    if not vacant_units.exists():
        return "There are currently no vacant units in the portfolio."

    result = [f"- {u.name} (Property: {u.asset.name})" for u in vacant_units]
    return "Vacant Units:\n" + "\n".join(result)


@tool("get_lease_expirations", args_schema=ExpiryInput)
def get_lease_expirations(workspace_id: str, days_out: int = 90) -> str:
    """Retrieves a list of active leases expiring within the specified number of days."""
    from rentals.models import Tenancy

    target_date = now().date() + timedelta(days=days_out)
    expiring = Tenancy.objects.filter(
        workspace_id=workspace_id,
        status='ACTIVE',
        end_date__lte=target_date,
        end_date__gte=now().date()
    ).select_related('unit', 'unit__asset')

    if not expiring.exists():
        return f"No leases are expiring in the next {days_out} days."

    result = [f"- {t.unit.name} ({t.unit.asset.name}): Expiring on {t.end_date}" for t in expiring]
    return f"Leases expiring within {days_out} days:\n" + "\n".join(result)


@tool("get_active_tenants", args_schema=UnitInput)
def get_active_tenants(workspace_id: str, unit_name: str = None) -> str:
    """Retrieves contact information and lease status for active tenants, optionally filtered by a specific unit."""
    from rentals.models import Tenancy

    queryset = Tenancy.objects.filter(workspace_id=workspace_id, status='ACTIVE').select_related('unit', 'tenant')

    if unit_name:
        queryset = queryset.filter(unit__name__icontains=unit_name)

    if not queryset.exists():
        return "No active tenants found matching the criteria."

    result = [f"- {t.tenant.first_name} {t.tenant.last_name} | Unit: {t.unit.name} | Phone: {t.tenant.phone}" for t in
              queryset]
    return "Active Tenants:\n" + "\n".join(result)


@tool("get_property_metrics", args_schema=WorkspaceInput)
def get_property_metrics(workspace_id: str) -> str:
    """Retrieves high-level portfolio metrics: total units, active leases, and occupancy rate."""
    from assets.models import Unit
    from rentals.models import Tenancy

    total_units = Unit.objects.filter(asset__workspace_id=workspace_id).count()
    active_leases = Tenancy.objects.filter(workspace_id=workspace_id, status='ACTIVE').count()

    if total_units == 0:
        return "No properties or units are registered in this portfolio."

    occupancy_rate = round((active_leases / total_units) * 100, 1)

    return (
        f"Portfolio Metrics:\n"
        f"- Total Units: {total_units}\n"
        f"- Active Leases: {active_leases}\n"
        f"- Occupancy Rate: {occupancy_rate}%"
    )

# 3. Export a list of all registered tools for the Copilot agent
COPILOT_TOOLS = [
    get_vacant_units,
    get_lease_expirations,
    get_active_tenants,
    get_property_metrics,
]
