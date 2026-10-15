from django.db import models
from workspaces.models import Workspace  # 🟢 Updated import
from assets.models import Assets
from accounts.models import User


class VerificationDocument(models.Model):
    file = models.FileField(upload_to="verification_docs/")
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)


# 🟢 CHANGED: Replaced OrganisationVerification with WorkspaceVerification
class WorkspaceVerification(models.Model):
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.CASCADE,
        related_name="verification"
    )
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    # You might want to switch this to a ManyToMany field like in PropertyVerification
    # so a business can upload multiple docs (ID, Business License, etc.)
    document = models.FileField(upload_to="verification_docs/")

    submitted_at = models.DateTimeField(auto_now_add=True)

    # 🟢 KEPT: The human Admin at QuestNest who reviewed the document
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Verification for {self.workspace.name}"


class PropertyVerification(models.Model):
    asset = models.OneToOneField(
        Assets,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="verification"
    )
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    documents = models.ManyToManyField(VerificationDocument, blank=True)

    # 🟢 KEPT: The human Admin at QuestNest who reviewed the document
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        asset_name = self.asset.name if self.asset else "Unknown Asset"
        return f"Verification for {asset_name}"


class AssetVerification(models.Model):
    """Verifies the ownership of a Physical Asset (Property)."""
    asset = models.OneToOneField(Assets, on_delete=models.CASCADE, related_name='asset_verification')
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    documents = models.ManyToManyField('VerificationDocument')