from django.db import migrations


DEFAULT_TASK_TAGS = [
    {"name": "Urgent", "color": "#f43f5e"},
    {"name": "Follow Up", "color": "#0ea5e9"},
    {"name": "Admin", "color": "#f59e0b"},
    {"name": "Finance", "color": "#10b981"},
    {"name": "Sales", "color": "#8b5cf6"},
]


def add_default_task_tags(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Tag = apps.get_model("projects", "Tag")

    for project in Project.objects.all():
        if Tag.objects.filter(project=project).exists():
            continue
        Tag.objects.bulk_create(
            Tag(project=project, name=tag["name"], color=tag["color"])
            for tag in DEFAULT_TASK_TAGS
        )


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0004_project_business"),
    ]

    operations = [
        migrations.RunPython(add_default_task_tags, migrations.RunPython.noop),
    ]
