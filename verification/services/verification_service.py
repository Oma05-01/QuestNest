from verification.models import WorkspaceVerification, AssetVerification, VerificationDocument
from operations.constants import EventType
from operations.services.event_service import log_event

def submit_workspace_verification(*, workspace, document_file, submitter):
    # Now WorkspaceVerification is defined!
    verification, created = WorkspaceVerification.objects.get_or_create(
        workspace=workspace
    )
    verification.document = document_file
    verification.verified = False
    verification.save()

    # Now log_event accepts 'workspace'!
    log_event(
        workspace=workspace,
        actor=submitter,
        event_type=EventType.WORKSPACE_VERIFICATION_SUBMITTED,
        object_type="WorkspaceVerification",
        object_id=str(verification.id)
    )
    return verification

def submit_asset_verification(*, asset, document_files, submitter):
    # Now AssetVerification is defined!
    verification, created = AssetVerification.objects.get_or_create(
        asset=asset
    )
    verification.verified = False
    verification.save()

    for file in document_files:
        doc = VerificationDocument.objects.create(file=file, name=file.name)
        verification.documents.add(doc)

    log_event(
        workspace=asset.workspace, # Pulling workspace context from the asset
        actor=submitter,
        event_type=EventType.ASSET_VERIFICATION_SUBMITTED,
        object_type="AssetVerification",
        object_id=str(verification.id)
    )
    return verification