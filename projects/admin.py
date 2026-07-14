from django.contrib import admin

from .models import Project, Tag, Task, TaskList, TaskNote


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "status", "created_at", "updated_at")
    list_filter = ("business", "status")
    search_fields = ("name", "description", "business__name")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "color")
    list_filter = ("project",)
    search_fields = ("name", "project__name")


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "created_at")
    list_filter = ("project",)
    search_fields = ("name", "description", "project__name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "list", "priority", "status", "due_date", "updated_at")
    list_filter = ("priority", "status", "list__project")
    search_fields = ("title", "description", "list__name", "list__project__name")
    filter_horizontal = ("tags",)


@admin.register(TaskNote)
class TaskNoteAdmin(admin.ModelAdmin):
    list_display = ("task", "created_at")
    search_fields = ("task__title", "content")
