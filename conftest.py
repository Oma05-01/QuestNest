import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from workspaces.models import Organisation
from wallet.models import Wallet, WalletTransaction
from assets.models import Assets, Unit
from rentals.models import Tenancy


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def organisation():
    return Organisation.objects.create(name="QuestNest Core", is_verified=True)


@pytest.fixture
def landlord(db):
    user = User.objects.create(email="landlord@test.com", role="landlord", name="Larry Landlord")
    user.set_password("password123")
    user.save()
    Wallet.objects.create(user=user)  # Create empty wallet
    return user


@pytest.fixture
def funded_tenant(db):
    user = User.objects.create(email="tenant@test.com", role="tenant", name="Terry Tenant")
    user.set_password("password123")
    user.save()

    # Give the tenant some money to test payments
    wallet = Wallet.objects.create(user=user)
    WalletTransaction.objects.create(
        wallet=wallet,
        amount=Decimal("5000.00"),
        transaction_type=WalletTransaction.CREDIT,
        reference="TEST-FUNDING-1"
    )
    return user


@pytest.fixture
def active_tenancy(db, organisation, landlord, funded_tenant):
    asset = Assets.objects.create(
        organisation=organisation, owner=landlord, name="Test Estate", status="listed"
    )
    unit = Unit.objects.create(
        asset=asset, name="Unit 1A", rent_amount=Decimal("1000.00"), status="occupied"
    )

    tenancy = Tenancy.objects.create(
        organisation=organisation,
        unit=unit,
        tenant=funded_tenant,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=365),
        status=Tenancy.ACTIVE,
        rent_amount=Decimal("1000.00"),
        next_payment_date=timezone.now().date()
    )
    return tenancy


@pytest.fixture(autouse=True)
def celery_always_eager(settings):
    """
    Forces Celery to run synchronously during tests so we can assert background tasks.
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

@pytest.fixture
def user(db):
    """
    Creates a basic, generic user.
    Needed for standalone Wallet unit tests.
    """
    user = User.objects.create(
        email="generic@test.com",
        name="Generic User",
        role="tenant"
    )
    user.set_password("password123")
    user.save()
    return user

@pytest.fixture
def wallet(user):
    """Creates a wallet for the generic user."""
    # We use get_or_create in case your User model has a
    # signal that automatically creates a wallet on save.
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet