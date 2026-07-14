from django.db import models
from projects.models import Project

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title
