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
    print("Starting Phase 2: Lease RAG Query Test...")
    print("-" * 50)

    # 1. Fetch Test User, Workspace, and Tenancy
    user = User.objects.filter(email='landlord_3@example.com').first()
    if not user:
        print("❌ Test user 'landlord_3@example.com' not found.")
        return

    workspace = Workspace.objects.filter(members__user=user).first() or Workspace.objects.first()
    if not workspace:
        print("❌ No workspace found for user.")
        return

    # Dynamically grab the exact same tenancy you used for the upload script
    tenancy = Tenancy.objects.filter(workspace=workspace).first()

    print(f"✓ Active Workspace: '{workspace.name}' (ID: {workspace.id})")
    print(f"✓ Authenticated User: {user.email}")
    print(f"✓ Target Tenancy ID: {tenancy.id}")

    # 2. Setup Headers & URL (matching the live server port 8001)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    url = 'http://localhost:8001/api/v1/ai/lease/query/'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Workspace-Id': str(workspace.id),
        'Content-Type': 'application/json'
    }

    # 3. Define Query Payload
    payload = {
        "tenancy_id": tenancy.id,
        "query": "What is the policy regarding pets and what is the security deposit amount?"
    }

    print(f"\nSending Query: '{payload['query']}'")
    print(f"Targeting Endpoint: {url}...")

    # 4. Execute Real HTTP POST Request
    try:
        response = requests.post(url, headers=headers, json=payload)

        print(f"\nHTTP Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 50)
            print("🤖 GROQ AI RESPONSE:")
            print("=" * 50)
            print(data.get("answer"))
            print("\n" + "-" * 50)
            print("📚 RETRIEVED SOURCES (pgvector):")
            print("-" * 50)
            for source in data.get("sources", []):
                print(
                    f"  • Chunk ID: {source.get('chunk_id')} | Page: {source.get('page_number')} | Distance: {source.get('distance')}")
            print("=" * 50)
        else:
            print("❌ Request failed!")
            print(f"Response Body: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure your Django server is running on port 8001.")


if __name__ == "__main__":
    run_test()