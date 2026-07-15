DEFAULT_TASK_TAGS = [
    {"name": "Urgent", "color": "#f43f5e"},
    {"name": "Follow Up", "color": "#0ea5e9"},
    {"name": "Admin", "color": "#f59e0b"},
    {"name": "Finance", "color": "#10b981"},
    {"name": "Sales", "color": "#8b5cf6"},
]


def ensure_default_task_tags(project):
    if project.tags.exists():
        return

    from .models import Tag

    Tag.objects.bulk_create(
        Tag(project=project, name=tag["name"], color=tag["color"])
        for tag in DEFAULT_TASK_TAGS
    )
