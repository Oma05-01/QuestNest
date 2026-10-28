import os
import django
import requests
import json

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from workspaces.models import Workspace
from rentals.models import Tenancy

User = get_user_model()


def run_test():
    print("-" * 50)
    print("Starting Phase 1 & 2: RAG-Enabled Triage Test...")
    print("-" * 50)

    # 1. Fetch Test User and Workspace
    user = User.objects.filter(email='landlord_3@example.com').first()
    if not user:
        print("❌ Test user 'landlord_3@example.com' not found.")
        return

    workspace = Workspace.objects.filter(members__user=user).first() or Workspace.objects.first()
    if not workspace:
        print("❌ No workspace found for user.")
        return

    # 2. Fetch the exact Unit tied to the Tenancy we uploaded the lease for
    tenancy = Tenancy.objects.filter(workspace=workspace).first()  # Should be ID 38 based on previous tests
    unit = tenancy.unit

    print(f"✓ Active Workspace: '{workspace.name}' (ID: {workspace.id})")
    print(f"✓ Target Unit: {unit.name} (ID: {unit.id})")

    # 3. Setup Headers & URL (matching port 8001)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Note: Ensure this URL matches your urls.py path for MaintenanceTriageView
    url = 'http://localhost:8001/api/v1/ai/triage/'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Workspace-Id': str(workspace.id),
        'Content-Type': 'application/json'
    }

    # 4. Define Query Payload
    # We use a plumbing issue since standard leases usually dictate who is responsible for clogs vs pipe bursts
    payload = {
        "unit_id": str(unit.id),
        "description": "The kitchen sink pipe suddenly burst underneath the cabinet and water is flooding the floor."
    }

    print(f"\nSending Triage Request: '{payload['description']}'")

    # 5. Execute HTTP POST Request
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"HTTP Response Status: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            triage_data = data.get("triage", {})

            print("\n" + "=" * 50)
            print("🤖 AI TRIAGE RESULT:")
            print("=" * 50)
            print(f"Ticket ID:      {data.get('ticket_id')}")
            print(f"Title:          {triage_data.get('suggested_title')}")
            print(f"Category:       {triage_data.get('category')}")
            print(f"Urgency:        {triage_data.get('urgency').upper()}")
            print("-" * 50)
            print(f"Summary:        {triage_data.get('summary')}")
            print(f"Severity:       {triage_data.get('severity')}")
            print("-" * 50)
            print(f"Landlord Resp?: {triage_data.get('is_landlord_responsible')}")
            print(f"Reasoning:      {triage_data.get('responsibility_reasoning')}")
            print("=" * 50)
        else:
            print("❌ Request failed!")
            print(f"Response Body: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure your Django server is running on port 8001.")


if __name__ == "__main__":
    run_test()