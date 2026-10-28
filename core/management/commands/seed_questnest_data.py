import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from accounts.models import User
from workspaces.models import Workspace, Membership
from assets.models import Assets, Unit
from rentals.models import Tenancy
from leases.models import LeaseAgreement
from maintenance.models import MaintenanceRequest, Vendor, MaintenanceAssignment
from payments.models import Payment


class Command(BaseCommand):
    help = "Seeds QuestNest database with realistic multi-tenant data for testing and AI workflows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--workspaces",
            type=int,
            default=3,
            help="Number of isolated workspaces to create (default: 3)",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete existing data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker()
        num_workspaces = options["workspaces"]

        if options["clean"]:
            self.stdout.write(self.style.WARNING("Cleaning existing database records..."))
            Payment.objects.all().delete()
            MaintenanceAssignment.objects.all().delete()
            MaintenanceRequest.objects.all().delete()
            Vendor.objects.all().delete()
            LeaseAgreement.objects.all().delete()
            Tenancy.objects.all().delete()
            Unit.objects.all().delete()
            Assets.objects.all().delete()
            Membership.objects.all().delete()
            Workspace.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            # Note: Add LeaseChunk and LeaseDocument deletes here if you want them cleared too
            self.stdout.write(self.style.SUCCESS("Database cleaned successfully.\n"))

        self.stdout.write(self.style.MIGRATE_HEADING(f"Seeding {num_workspaces} Workspaces..."))

        MAINTENANCE_ISSUES = [
            ("Water leak in bathroom", "Active water leaking under the sink, causing dampness on cabinet floor.",
             "high"),
            ("Electrical panel tripping", "Circuit breaker keeps tripping whenever the AC is turned on.", "high"),
            ("AC blowing warm air", "Air conditioner unit blowing warm air in the living room.", "medium"),
            ("Door lock mechanism jammed", "Front entrance door lock is loose and hard to latch.", "urgent"),
            ("Low water pressure", "Shower in primary bathroom has very low water pressure.", "medium"),
            ("Kitchen light flickering", "Main kitchen fixture lights flicker continuously.", "low"),
            ("Peeling ceiling paint", "Paint is peeling off the ceiling in the guest bedroom due to humidity.", "low"),
            ("Clogged gutter", "Rainwater is overflowing from the front roof gutters.", "medium"),
        ]

        for w_idx in range(num_workspaces):
            # 1. Workspace
            company_name = fake.company()
            workspace = Workspace.objects.create(
                name=f"{company_name} Properties",
                workspace_type=Workspace.BUSINESS,
                is_verified=True,
            )

            # 2. Landlord / Owner User (Guarantees landlord_1, landlord_2, landlord_3 are created)
            landlord_email = f"landlord_{w_idx + 1}@example.com"
            landlord = User.objects.create_user(
                email=landlord_email,
                password="Password123!",
                name=fake.name(),
            )
            Membership.objects.create(
                workspace=workspace,
                user=landlord,
                role=Membership.OWNER,
            )

            # 3. Vendors
            plumber = Vendor.objects.create(
                workspace=workspace,
                name=f"{fake.last_name()} Plumbing Services",
                category=Vendor.PLUMBING,
                phone=fake.phone_number()[:20],
                email=fake.email(),
            )
            electrician = Vendor.objects.create(
                workspace=workspace,
                name=f"{fake.last_name()} Electrical Co.",
                category=Vendor.ELECTRICAL,
                phone=fake.phone_number()[:20],
                email=fake.email(),
            )
            hvac = Vendor.objects.create(
                workspace=workspace,
                name=f"{fake.last_name()} Heating & Cooling",
                category="HVAC",  # Assuming free-text or a choice you have configured
                phone=fake.phone_number()[:20],
                email=fake.email(),
            )

            self.stdout.write(self.style.SUCCESS(
                f"▶ Created Workspace #{workspace.id}: '{workspace.name}' (Owner: {landlord.email})"))

            # 4. Assets & Units (Increased density)
            for _ in range(random.randint(3, 5)):
                asset = Assets.objects.create(
                    workspace=workspace,
                    name=f"{fake.city()} Apartments",
                    location=fake.address(),
                    status=Assets.OCCUPIED,
                )

                for u_idx in range(1, random.randint(4, 7)):
                    monthly_rent = Decimal(random.randint(150000, 750000))
                    unit = Unit.objects.create(
                        asset=asset,
                        name=f"Unit {100 + u_idx}",
                        status=Unit.OCCUPIED,
                        rent_amount=monthly_rent,
                    )

                    # 5. Tenant User
                    tenant = User.objects.create_user(
                        email=fake.unique.email(),
                        password="Password123!",
                        name=fake.name(),
                    )
                    Membership.objects.create(
                        workspace=workspace,
                        user=tenant,
                        role=Membership.MEMBER,
                    )

                    # 6. Tenancy Record (Past & Active Variation)
                    start_date = timezone.now().date() - timedelta(days=random.randint(30, 300))
                    end_date = start_date + timedelta(days=365)
                    deposit = monthly_rent * Decimal("1.5")

                    is_active = random.choice([True, True, False])  # Lean towards active

                    tenancy = Tenancy.objects.create(
                        workspace=workspace,
                        unit=unit,
                        tenant=tenant,
                        start_date=start_date,
                        end_date=end_date,
                        rent_amount=monthly_rent,
                        deposit_amount=deposit,
                        status=Tenancy.ACTIVE if is_active else "TERMINATED",  # Adjust to match your model's choices
                    )

                    # 7. Lease Agreement
                    lease = LeaseAgreement.objects.create(
                        workspace=workspace,
                        tenancy=tenancy,
                        rent_amount=monthly_rent,
                        deposit_amount=deposit,
                        start_date=start_date,
                        end_date=end_date,
                        status=LeaseAgreement.ACTIVE if is_active else "EXPIRED",
                    )

                    # 8. Maintenance Request
                    if random.choice([True, False, True]):  # Higher chance to have issues
                        title, desc, priority = random.choice(MAINTENANCE_ISSUES)
                        # Fixed the string formatting issue here
                        req_title = f"{title} - {unit.name}"

                        req = MaintenanceRequest.objects.create(
                            workspace=workspace,
                            unit=unit,
                            tenant=tenant,
                            title=req_title,
                            description=desc,
                            priority=priority,
                            status=random.choice([
                                MaintenanceRequest.OPEN,
                                MaintenanceRequest.IN_PROGRESS,
                                "RESOLVED"
                            ]),
                            estimated_cost=Decimal(random.randint(10000, 50000)),
                        )

                        if req.status in [MaintenanceRequest.IN_PROGRESS, "RESOLVED"]:
                            # Smart dispatch based on keywords
                            if "Water" in title or "pressure" in title:
                                v = plumber
                            elif "Electrical" in title or "light" in title:
                                v = electrician
                            elif "AC" in title:
                                v = hvac
                            else:
                                v = random.choice([plumber, electrician, hvac])

                            MaintenanceAssignment.objects.create(
                                request=req,
                                vendor=v,
                                cost=req.estimated_cost,
                                notes="Assigned via automated system.",
                            )

                    # 9. Payments (Varying statuses)
                    for m in range(random.randint(2, 6)):
                        Payment.objects.create(
                            workspace=workspace,
                            user=tenant,
                            tenancy=tenancy,
                            reference=f"PAY-{uuid.uuid4().hex[:10].upper()}",
                            amount=lease.rent_amount,
                            status=random.choice(
                                [Payment.SUCCESS, Payment.SUCCESS, Payment.SUCCESS, "FAILED", "PENDING"]),
                        )

        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully seeded QuestNest database with {num_workspaces} workspaces and rich dummy data!"))