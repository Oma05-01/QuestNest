from django.db.models import Sum, Count, Q
from django.utils import timezone
from rentals.models import Tenancy
from payments.models import Payment
from assets.models import Unit
from operations.models import Event


# --- TENANT DASHBOARD ---
def get_tenant_dashboard_data(user):
    # 🟢 OPTIMIZATION: select_related('unit') fetches unit data in the SAME query.
    # No more separate DB hits for unit name or details.
    tenancy = Tenancy.objects.select_related('unit').filter(tenant=user, status='active').first()

    total_paid = Payment.objects.filter(user=user, status='success').aggregate(Sum('amount'))['amount__sum'] or 0

    return {
        "tenancy": {
            # This is now an "instant" lookup because of select_related
            "unit": tenancy.unit.name if tenancy else None,
            "next_due": tenancy.next_payment_date if tenancy else None,
            "rent_amount": tenancy.rent_amount if tenancy else 0,
        },
        "balance": {
            "outstanding": tenancy.get_outstanding_balance() if tenancy else 0,
            "total_paid": total_paid,
        },
        # 🟢 OPTIMIZATION: .only() limits the SQL query to only these fields
        "recent_payments": Payment.objects.filter(user=user).order_by('-created_at')[:5].only(
            'id', 'reference', 'amount', 'status', 'created_at'
        ).values('id', 'reference', 'amount', 'status', 'created_at')
    }


# --- LANDLORD DASHBOARD ---
def get_landlord_dashboard_data(user):
    org = user.organisation

    # 🟢 OPTIMIZATION: We don't need the whole Unit object, just the stats.
    # Aggregates stay as they are—they are already DB-level efficient.
    stats = Unit.objects.filter(asset__organisation=org).aggregate(
        total_units=Count('id'),
        occupied=Count('id', filter=Q(status='occupied')),
        vacant=Count('id', filter=Q(status='vacant'))
    )

    total_revenue = Payment.objects.filter(
        organisation=org,
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return {
        "portfolio_summary": stats,
        "financials": {
            "total_revenue": total_revenue,
            # .count() is efficient (SELECT COUNT(*) ...)
            "pending_invoices": Payment.objects.filter(organisation=org, status='pending').count()
        },
        "overdue_tenants": Tenancy.objects.filter(
            organisation=org,
            status='active',
            next_payment_date__lt=timezone.now().date()
        ).count()
    }


# --- ADMIN (SYSTEM) DASHBOARD ---
def get_admin_dashboard_data(user):
    yesterday = timezone.now() - timezone.timedelta(days=1)

    return {
        "system_health": {
            "total_events_24h": Event.objects.filter(created_at__gte=yesterday).count(),
            "failed_events": Event.objects.filter(status='failed').count(),
        },
        "growth_metrics": {
            # Use .filter().count() instead of querying all and counting in Python
            "total_verified_orgs": user.organisation.__class__.objects.filter(is_verified=True).count(),
            "global_revenue": Payment.objects.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0
        }
    }