import uuid
from pathlib import Path

from django.db import models
from projects.models import Project


def attachment_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"attachments/{instance.business_id or 'unassigned'}/{uuid.uuid4().hex}{extension}"

class Document(models.Model):
    """
    Holds long-form notes, wiki logs, plans, and business receipts metadata.
    Supports markdown content fields and links to specific projects.
    """
    business = models.ForeignKey('accounts.Business', related_name='documents', on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(
        Project, 
        related_name='documents', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Write notes using standard Markdown.")
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-pinned_at', '-updated_at']

    def __str__(self):
        return self.title


class DocumentAttachment(models.Model):
    """
    Uploaded files that can stand alone in the document library or attach to
    project follow-up notes for context.
    """
    business = models.ForeignKey('accounts.Business', related_name='attachments', on_delete=models.CASCADE)
    document = models.ForeignKey(Document, related_name='attachments', on_delete=models.CASCADE, null=True, blank=True)
    task_note = models.ForeignKey('projects.TaskNote', related_name='attachments', on_delete=models.CASCADE, null=True, blank=True)
    uploaded_by = models.ForeignKey('auth.User', related_name='uploaded_attachments', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=attachment_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.title or self.original_filename

    @property
    def extension(self):
        return Path(self.original_filename).suffix.lower().lstrip('.') or 'file'

    @property
    def size_label(self):
        if self.size >= 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        if self.size >= 1024:
            return f"{self.size / 1024:.1f} KB"
        return f"{self.size} B"
