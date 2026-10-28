# ai/models.py
from django.db import models
from core.models import BaseModel
from pgvector.django import VectorField
from rentals.models import Tenancy
from workspaces.models import Workspace


class AIRun(BaseModel):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="ai_runs"
    )
    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    task = models.CharField(max_length=50)  # e.g., 'triage', 'lease_qa'
    model_name = models.CharField(max_length=100)

    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)

    status = models.CharField(max_length=20, default="success")  # success, failed
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.task} ({self.model_name}) - WS #{self.workspace_id}"


class LeaseDocument(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)
    file = models.FileField(upload_to='leases/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="pending")  # pending, processing, completed


class LeaseChunk(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    document = models.ForeignKey(LeaseDocument, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()

    # 384 or 1536 depending on your chosen embedding model
    embedding = VectorField(dimensions=384)
    chunk_index = models.IntegerField()