from verification.models import OrganisationVerification, PropertyVerification, VerificationDocument
from operations.constants import EventType
from operations.services.event_service import log_event


def submit_organisation_verification(*, organisation, document_file, submitter):
    """Handles uploading a single document for an organisation."""

    # Use get_or_create so they can re-submit if previously rejected
    verification, created = OrganisationVerification.objects.get_or_create(
        organisation=organisation
    )
    verification.document = document_file
    verification.verified = False  # Reset to false on new submission
    verification.save()

    log_event(
        organisation=organisation,
        actor=submitter,
        event_type="ORG_VERIFICATION_SUBMITTED",  # Add to your EventType constants
        object_type="OrganisationVerification",
        object_id=str(verification.id)
    )
    return verification


def submit_property_verification(*, asset, document_files, submitter):
    """Handles uploading multiple documents for a property."""

    verification, created = PropertyVerification.objects.get_or_create(
        asset=asset
    )
    verification.verified = False
    verification.save()

    # Create the individual document records and attach them
    for file in document_files:
        doc = VerificationDocument.objects.create(file=file, name=file.name)
        verification.documents.add(doc)

    log_event(
        organisation=asset.organisation,
        actor=submitter,
        event_type="PROPERTY_VERIFICATION_SUBMITTED",  # Add to your EventType constants
        object_type="PropertyVerification",
        object_id=str(verification.id)
    )
    return verification