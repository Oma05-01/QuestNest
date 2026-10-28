import os
import django
import requests

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from workspaces.models import Workspace
from rentals.models import Tenancy

User = get_user_model()


def run_api_test():
    print("-" * 50)
    print("Starting Phase 4: Escrow API Integration Test")
    print("-" * 50)

    # 1. Fetch Test User, Workspace, and Tenancy
    user = User.objects.filter(email='landlord_3@example.com').first()
    if not user:
        print("❌ Test user not found.")
        return

    workspace = Workspace.objects.filter(members__user=user).first()
    tenancy = Tenancy.objects.filter(workspace=workspace).order_by('-id').first()

    if not tenancy:
        print("❌ No active tenancy found for this workspace.")
        return

    print(f"✓ Active Workspace: '{workspace.name}'")
    print(f"✓ Target Tenancy ID: {tenancy.id}")

    # 2. Setup Headers & URLs
    refresh = RefreshToken.for_user(user)
    headers = {
        'Authorization': f'Bearer {refresh.access_token}',
        'X-Workspace-Id': str(workspace.id),
        'Content-Type': 'application/json'
    }

    base_url = f'http://localhost:8001/api/v1/ai/escrow/{tenancy.id}'

    # 3. Trigger the Start Endpoint
    print("\n▶️ [POST] /start/ - Triggering AI Analysis & Pause...")
    start_response = requests.post(f'{base_url}/start/', headers=headers)

    if start_response.status_code == 200:
        data = start_response.json()
        print("\n⏸️ GRAPH PAUSED. AI RESPONSE:")
        print(f"Status:       {data.get('status')}")
        print(f"Confidence:   {data.get('confidence_score')}")
        print(f"Reasoning:    {data.get('recommendation')}")
    else:
        print(f"❌ Start API Failed: {start_response.status_code} - {start_response.text}")
        return

    # 4. Trigger the Resolve Endpoint (Simulate Human Approval)
    print("\n👤 Simulating Landlord clicking 'Approve'...")
    print("▶️ [POST] /resolve/ - Resuming the Graph...")

    resolve_payload = {"approved": True}
    resolve_response = requests.post(f'{base_url}/resolve/', headers=headers, json=resolve_payload)

    if resolve_response.status_code == 200:
        data = resolve_response.json()
        print("\n✅ GRAPH FINALIZED. FINAL STATE:")
        print(f"Status:       {data.get('status')}")
        print(f"Approved:     {data.get('human_approved')}")
        print(f"Final Text:   {data.get('recommendation')}")
    else:
        print(f"❌ Resolve API Failed: {resolve_response.status_code} - {resolve_response.text}")


if __name__ == "__main__":
    run_api_test()