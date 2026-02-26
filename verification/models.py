from django.db import models
from organisations.models import Organisation
from assets.models import Assets
from accounts.models import User

class VerificationDocument(models.Model):
    file = models.FileField(upload_to="verification_docs/")
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class OrganisationVerification(models.Model):
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    document = models.FileField(upload_to="verification_docs/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

class PropertyVerification(models.Model):
    asset = models.OneToOneField(Assets, on_delete=models.CASCADE, null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    documents = models.ManyToManyField(VerificationDocument, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
