# test_lease_upload.py
import os
import django
import json
import io
import requests  # <-- We will use the requests library for a real HTTP call
from reportlab.pdfgen import canvas

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from workspaces.models import Workspace
from rentals.models import Tenancy
from ai.models import LeaseDocument


def run_test():
    print("-" * 50)
    print("Starting Phase 2: Lease RAG Upload Test...")
    print("-" * 50)

    # 1. Setup Auth & Workspace
    email = "landlord_3@example.com"
    user = User.objects.get(email=email)

    # Grab the first workspace associated with this user
    workspace = Workspace.objects.filter(members__user=user).first() or Workspace.objects.first()
    print(f"✓ Using Active Workspace: '{workspace.name}' (ID: {workspace.id})")
    print(f"✓ Authenticated as: {email}")

    # 2. Locate a valid Tenancy
    tenancy = Tenancy.objects.filter(workspace=workspace).first()
    if not tenancy:
        print(f"❌ Error: No tenancies found in workspace '{workspace.name}'.")
        return

    print(f"✓ Target Tenancy ID: {tenancy.id}")

    # 3. Generate a minimal valid PDF in memory
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "Lease Agreement")
    c.drawString(100, 730, "Tenant: John Doe")
    c.drawString(100, 710, "Rent Amount: $2,000 per month")
    c.drawString(100, 690, "Security Deposit: $2,000 due upon signing.")
    c.drawString(100, 670, "Pets Policy: No pets allowed without written landlord approval.")
    c.save()

    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()

    # 4. Prepare Request
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Update port if your Django dev server is running on a different one
    url = 'http://127.0.0.1:8001/api/v1/ai/lease/upload/'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Workspace-Id': str(workspace.id)
    }

    data = {
        "tenancy_id": tenancy.id
    }

    files = {
        # (filename, binary_data, content_type)
        "file": ("valid_lease_agreement.pdf", pdf_bytes, "application/pdf")
    }

    print(f"\nSending real multipart POST request to {url}...")

    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        print(f"\nHTTP Response Status: {response.status_code}")

        if response.status_code == 202:
            print("✓ Lease Upload Succeeded and Celery Task Queued!\n")
            print("Returned Schema:")

            response_data = response.json()
            print(json.dumps(response_data, indent=2))

            # Verify it hit the database
            doc_id = response_data.get('document_id')
            if doc_id:
                doc = LeaseDocument.objects.get(id=doc_id)
                print(f"\nDatabase Verification: LeaseDocument {doc.id} is currently '{doc.status}'")

        else:
            print(f"❌ Request failed with payload: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure your Django server is running (python manage.py runserver).")


if __name__ == '__main__':
    run_test()