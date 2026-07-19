from django.contrib import admin

from .models import Document, DocumentAttachment


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "project", "created_at", "updated_at")
    list_filter = ("business", "project")
    search_fields = ("title", "content", "project__name", "business__name")


@admin.register(DocumentAttachment)
class DocumentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("display_name", "business", "document", "task_note", "uploaded_by", "size", "created_at")
    list_filter = ("business", "content_type", "created_at")
    search_fields = ("title", "original_filename", "document__title", "task_note__content", "business__name")
