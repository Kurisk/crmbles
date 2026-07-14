from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "project", "created_at", "updated_at")
    list_filter = ("business", "project")
    search_fields = ("title", "content", "project__name", "business__name")
