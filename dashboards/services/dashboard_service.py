from django.db.models import Sum, Count, Q
from django.utils import timezone
from rentals.models import Tenancy
from payments.models import Payment
from assets.models import Unit
from operations.models import Event
from workspaces.models import Workspace


# --- TENANT DASHBOARD (Personal Workspace) ---
def get_tenant_dashboard_data(user, workspace=None):
    # Filter tenancies for the user and active workspace context
    tenancy_qs = Tenancy.objects.select_related('unit').filter(tenant=user, status='active')
    if workspace:
        tenancy_qs = tenancy_qs.filter(workspace=workspace)

    tenancy = tenancy_qs.first()
    active_leases_count = tenancy_qs.count()

    # Filter completed payments
    payment_qs = Payment.objects.filter(
        Q(user=user) | Q(tenancy__tenant=user),
        status__in=['success', 'completed']
    )
    if workspace:
        payment_qs = payment_qs.filter(workspace=workspace)

    total_paid = payment_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    next_payment_date = tenancy.next_payment_date if tenancy else None

    return {
        # Flat keys expected by TenantDashboard.jsx
        "total_paid": float(total_paid),
        "next_rent_due": next_payment_date,
        "active_leases": active_leases_count,

        # Detailed nested objects for lease card details
        "tenancy": {
            "unit": tenancy.unit.name if tenancy and tenancy.unit else None,
            "next_due": next_payment_date,
            "rent_amount": float(tenancy.rent_amount) if tenancy and hasattr(tenancy, 'rent_amount') else 0,
        },
        "balance": {
            "outstanding": float(tenancy.get_outstanding_balance()) if tenancy and hasattr(tenancy, 'get_outstanding_balance') else 0,
            "total_paid": float(total_paid),
        },
        "recent_payments": payment_qs.order_by('-created_at')[:5].only(
            'id', 'reference', 'amount', 'status', 'created_at'
        ).values('id', 'reference', 'amount', 'status', 'created_at')
    }


# --- LANDLORD DASHBOARD (Business Workspace) ---
def get_landlord_dashboard_data(user, workspace=None):
    unit_qs = Unit.objects.all()
    payment_qs = Payment.objects.filter(status__in=['success', 'completed'])
    tenancy_qs = Tenancy.objects.filter(status='active')

    if workspace:
        unit_qs = unit_qs.filter(asset__workspace=workspace)
        payment_qs = payment_qs.filter(workspace=workspace)
        tenancy_qs = tenancy_qs.filter(workspace=workspace)

    stats = unit_qs.aggregate(
        total_units=Count('id'),
        occupied=Count('id', filter=Q(status='occupied')),
        vacant=Count('id', filter=Q(status='vacant'))
    )

    total_revenue = payment_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    return {
        "total_revenue": float(total_revenue),
        "escrow_balance": float(total_revenue),  # Update with escrow wallet logic when connected
        "active_tenants": tenancy_qs.count(),
        "portfolio_summary": stats,
        "financials": {
            "total_revenue": float(total_revenue),
            "pending_invoices": Payment.objects.filter(
                workspace=workspace, status='pending'
            ).count() if workspace else 0
        },
        "overdue_tenants": tenancy_qs.filter(
            next_payment_date__lt=timezone.now().date()
        ).count()
    }


# --- ADMIN (SYSTEM) DASHBOARD ---
def get_admin_dashboard_data(user):
    yesterday = timezone.now() - timezone.timedelta(days=1)

    global_revenue = Payment.objects.filter(
        status__in=['success', 'completed']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return {
        "total_users": user.__class__.objects.count(),
        "active_escrows": Payment.objects.filter(status='escrow_held').count(),
        "system_health": "OPERATIONAL",
        "activity_metrics": {
            "total_events_24h": Event.objects.filter(created_at__gte=yesterday).count(),
            "failed_events": Event.objects.filter(status='failed').count(),
        },
        "growth_metrics": {
            "total_verified_orgs": Workspace.objects.filter(is_verified=True).count(),
            "global_revenue": float(global_revenue)
        }
    }