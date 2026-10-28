import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')
django.setup()

from django.contrib.auth import get_user_model
from workspaces.models import Workspace
from rentals.models import Tenancy
from ai.escrow import escrow_app

User = get_user_model()


def run_db_update_test():
    print("-" * 50)
    print("Testing DB Transaction in Escrow Graph")
    print("-" * 50)

    # 1. Fetch a test user and an ACTIVE tenancy
    user = User.objects.filter(email='landlord_3@example.com').first()
    workspace = Workspace.objects.filter(members__user=user).first()

    # Grab the most recent active tenancy
    tenancy = Tenancy.objects.filter(workspace=workspace, status__iexact='active').order_by('-id').first()
    if not tenancy:
        print("❌ No ACTIVE tenancy found for this workspace. You may need to re-seed your database.")
        return

    print(f"✓ Target Tenancy ID: {tenancy.id}")
    print(f"📊 Initial DB Status:  {tenancy.status}")

    # 2. Setup the LangGraph configuration
    config = {"configurable": {"thread_id": f"escrow_db_test_{tenancy.id}"}}
    initial_state = {
        "tenancy_id": tenancy.id,
        "workspace_id": str(workspace.id),
        "human_approved": False
    }

    # 3. Run the graph until the breakpoint
    print("\n▶️ Running Graph to Breakpoint...")
    escrow_app.invoke(initial_state, config)

    # 4. Inject human approval and resume execution
    print("👤 Simulating Human Approval...")
    escrow_app.update_state(config, {"human_approved": True})

    print("▶️ Resuming Graph to Execute Database Update...")
    final_state = escrow_app.invoke(None, config)

    # 5. Refresh the instance from the PostgreSQL database
    tenancy.refresh_from_db()

    print("\n✅ [VERIFICATION COMPLETE]")
    print(f"Final Node Output:   {final_state.get('recommendation')[-65:]}")
    print(f"📊 Final DB Status:  {tenancy.status}")

    if tenancy.status == 'COMPLETED':
        print("\n🎉 Success! The LangGraph node successfully mutated the PostgreSQL database.")
    else:
        print("\n❌ Error: The database status did not update.")


if __name__ == "__main__":
    run_db_update_test()