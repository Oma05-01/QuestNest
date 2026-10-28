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

User = get_user_model()


def run_stream_test():
    print("-" * 50)
    print("Starting Phase 3: Copilot SSE Stream Test...")
    print("-" * 50)

    # 1. Fetch Test User and Workspace
    user = User.objects.filter(email='landlord_3@example.com').first()
    workspace = Workspace.objects.filter(members__user=user).first() or Workspace.objects.first()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    url = 'http://localhost:8001/api/v1/ai/copilot/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Workspace-Id': str(workspace.id),
        'Content-Type': 'application/json'
    }

    payload = {
        "message": (
            "Can you give me a quick summary of my portfolio metrics, "
            "and also tell me which leases are expiring in the next 45 days?"
        )
    }

    print(f"✓ Active Workspace: '{workspace.name}'")
    print(f"🗣️ User: '{payload['message']}'\n")
    print("🤖 COPILOT RESPONSE:")

    # 2. Execute POST request with stream=True
    with requests.post(url, headers=headers, json=payload, stream=True) as response:
        if response.status_code != 200:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return

        # 3. Parse the SSE stream in real-time
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')

                # SSE lines start with 'data: '
                if decoded_line.startswith('data: '):
                    json_str = decoded_line[6:]  # Strip 'data: ' prefix

                    try:
                        data = json.loads(json_str)
                        event_type = data.get('type')

                        if event_type == 'tool_start':
                            print(f"\n\n[🔧 USING TOOL: {data.get('tool')}]...\n")
                        elif event_type == 'content':
                            # Print text chunks dynamically without newlines
                            print(data.get('text'), end='', flush=True)
                        elif event_type == 'error':
                            print(f"\n\n[❌ ERROR]: {data.get('message')}")
                        elif event_type == 'done':
                            print("\n\n[✅ STREAM COMPLETE]")

                    except json.JSONDecodeError:
                        pass


if __name__ == "__main__":
    run_stream_test()