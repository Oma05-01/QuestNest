from django.db.models import Sum, Count, Q
from accounts.models import User
from wallet.models import Wallet, WalletTransaction
from rentals.models import Tenancy
from assets.models import Assets, Unit
from escrow.models import Escrow
from operations.models import Task, Event


def get_tenant_dashboard_data(user: User) -> dict:
    """
    Aggregates all necessary data for the Tenant dashboard.
    """
    # 1. Wallet Balance
    # Assuming a OneToOne field or fetching the first wallet for the user
    wallet = Wallet.objects.filter(user=user).first()
    wallet_balance = wallet.balance if wallet else 0.00

    # 2. Active Tenancy
    # Fetching the current active tenancy for this user
    active_tenancy = Tenancy.objects.filter(tenant=user, status="ACTIVE").select_related('unit', 'unit__asset').first()
    tenancy_data = None
    if active_tenancy:
        tenancy_data = {
            "tenancy_id": str(active_tenancy.id),
            "asset_name": active_tenancy.unit.asset.name,  # Adjust field name if needed
            "unit_name": active_tenancy.unit.name,
            "rent_amount": active_tenancy.rent_amount,
            "next_due_date": active_tenancy.next_due_date,  # Assuming this field exists
        }

    # 3. Action Items (Pending Tasks)
    pending_tasks = Task.objects.filter(
        assigned_to=user,
        status="pending"
    ).order_by('due_date')[:5].values('id', 'title', 'due_date')

    # 4. Recent Activity (Latest Wallet Transactions)
    recent_activity = []
    if wallet:
        recent_activity = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:5].values('transaction_type', 'amount', 'created_at', 'description')

    return {
        "wallet_balance": wallet_balance,
        "active_tenancy": tenancy_data,
        "action_items": list(pending_tasks),
        "recent_activity": list(recent_activity),
    }


def get_landlord_dashboard_data(user: User) -> dict:
    """
    Aggregates all necessary data for the Landlord dashboard.
    """
    # 1. Portfolio Summary
    # Assuming 'landlord' or 'owner' is a ForeignKey on the Asset model
    total_assets = Assets.objects.filter(landlord=user).count()

    # Aggregating unit statuses across all the landlord's assets
    unit_stats = Unit.objects.filter(asset__landlord=user).aggregate(
        total_units=Count('id'),
        occupied_units=Count('id', filter=Q(status='OCCUPIED')),
        vacant_units=Count('id', filter=Q(status='AVAILABLE'))
    )

    # 2. Financials
    wallet = Wallet.objects.filter(user=user).first()
    wallet_balance = wallet.balance if wallet else 0.00

    # Calculate total funds locked in Escrow for this landlord's units
    locked_in_escrow = Escrow.objects.filter(
        tenancy__unit__asset__landlord=user,
        status="FUNDED"  # Assuming 'FUNDED' means it's held and not yet released
    ).aggregate(total=Sum('amount'))['total'] or 0.00

    # 3. Action Items
    pending_tasks = Task.objects.filter(
        assigned_to=user,
        status="pending"
    ).order_by('due_date')[:5].values('id', 'title', 'due_date')

    # 4. Recent Activity (System events related to their properties)
    # This might require adjusting based on how you link events to landlords
    # For now, fetching tasks created for them or general system notifications
    recent_events = Event.objects.filter(
        actor=user
    ).order_by('-created_at')[:5].values('event_type', 'created_at')

    return {
        "portfolio": {
            "total_assets": total_assets,
            "total_units": unit_stats['total_units'] or 0,
            "occupied_units": unit_stats['occupied_units'] or 0,
            "vacant_units": unit_stats['vacant_units'] or 0,
        },
        "financials": {
            "wallet_balance": wallet_balance,
            "locked_in_escrow": locked_in_escrow,
        },
        "action_items": list(pending_tasks),
        "recent_activity": list(recent_events),
    }


def get_admin_dashboard_data(user: User) -> dict:
    """
    Aggregates high-level system metrics for the Admin dashboard.
    """
    # 1. System Health
    total_users = User.objects.count()
    tenant_count = User.objects.filter(role='tenant').count()
    landlord_count = User.objects.filter(role='landlord').count()
    active_tenancies = Tenancy.objects.filter(status="ACTIVE").count()

    # 2. Platform Financials
    # Sum of all successful wallet transactions (or just credits to see volume)
    total_volume = WalletTransaction.objects.filter(
        transaction_type='credit'
    ).aggregate(total=Sum('amount'))['total'] or 0.00

    # 3. System Monitor (Latest global events)
    recent_events = Event.objects.all().order_by('-created_at')[:10].values(
        'event_type', 'object_type', 'created_at'
    )

    return {
        "system_health": {
            "total_users": total_users,
            "tenants": tenant_count,
            "landlords": landlord_count,
            "active_tenancies": active_tenancies,
        },
        "platform_financials": {
            "total_volume_processed": total_volume,
        },
        "system_monitor": list(recent_events),
    }