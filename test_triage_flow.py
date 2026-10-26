import os
import django
import json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "questnest.settings")  # Adjust if settings file is located elsewhere (e.g. config.settings)
django.setup()

from rest_framework.test import APIClient
from workspaces.models import Workspace, Membership
from ai.models import AIRun


def run_test():
    print("--------------------------------------------------")
    print("Starting Phase 1 Maintenance Triage Test...")
    print("--------------------------------------------------")

    # 1. Fetch a seeded workspace
    workspace = Workspace.objects.first()
    if not workspace:
        print("❌ Error: No workspace found. Run `python manage.py seed_questnest_data` first.")
        return

    # 2. Find the owner/landlord user for this workspace
    membership = Membership.objects.filter(workspace=workspace, role=Membership.OWNER).first()
    if not membership:
        print(f"❌ Error: No owner membership found for Workspace '{workspace.name}'.")
        return

    user = membership.user
    print(f"✓ Using Active Workspace: '{workspace.name}' (ID: {workspace.id})")
    print(f"✓ Authenticated as: {user.email}")

    # 3. Setup Django REST Framework test client
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Setup Django REST Framework test client
    client = APIClient()
    from rentals.models import Tenancy
    from assets.models import Unit
    tenancy = Tenancy.objects.filter(workspace=workspace, status=Tenancy.ACTIVE).first()
    test_unit = Unit.objects.filter(asset__workspace=workspace).first()
    if not test_unit:
        print(f"❌ Error: No units found in workspace '{workspace.name}'.")
        return

    payload = {
        "description": (
            "Hi, there's water leaking heavily under the kitchen sink every time I run the faucet! "
            "It's soaking the wooden cabinet floor and starting to drip onto the kitchen tiles. "
            "Please send someone quickly before it damages the floorboards or causes mold."
        ),
        "unit_id": str(test_unit.id)
    }

    url = "/api/v1/ai/triage/"

    # Send BOTH the workspace ID and the Bearer token so the middleware can process them
    headers = {
        "HTTP_X_WORKSPACE_ID": str(workspace.id),
        "HTTP_AUTHORIZATION": f"Bearer {access_token}"
    }

    print(f"\nSending POST request to {url} with `X-Workspace-ID: {workspace.id}`...")

    # 5. Execute API call
    response = client.post(
        url,
        data=payload,
        format="json",
        HTTP_HOST="localhost",
        **headers
    )

    print(f"\nHTTP Response Status: {response.status_code}")

    if response.status_code in [200, 201]:
        print("✓ Triage Workflow Succeeded!\n")
        print("Returned Schema:")
        print(json.dumps(response.data, indent=2))
    else:
        # Safely print the error payload whether it's a DRF Response or raw HttpResponse
        error_content = getattr(response, 'data', response.content.decode('utf-8'))
        print(f"❌ Request failed with payload: {error_content}")


if __name__ == "__main__":
    run_test()