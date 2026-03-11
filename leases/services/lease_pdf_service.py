from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML

from leases.models import LeaseDocument
from operations.services.event_service import log_event
from operations.constants import EventType


def generate_lease_pdf(lease, actor=None):
    """
    Generate a PDF document for a lease agreement.
    """

    tenancy = lease.tenancy
    unit = tenancy.unit
    tenant = tenancy.tenant

    clauses = lease.clauses.order_by("order")

    context = {
        "lease": lease,
        "tenancy": tenancy,
        "unit": unit,
        "tenant": tenant,
        "organisation": lease.organisation,
        "clauses": clauses,
        "signatures": lease.signatures.all(),
    }

    html_string = render_to_string(
        "leases/lease_template.html",
        context
    )

    pdf_file = HTML(string=html_string).write_pdf()

    filename = f"lease_{lease.id}.pdf"

    document = LeaseDocument.objects.create(
        lease=lease,
        file=ContentFile(pdf_file, name=filename),
        version=1
    )

    log_event(
        organisation=lease.organisation,
        actor=actor,
        event_type=EventType.LEASE_PDF_GENERATED,
        object_type="LeaseAgreement",
        object_id=str(lease.id),
        metadata={
            "document_id": document.id
        }
    )

    return document