from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0006_project_task_pins"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="tasknote",
            options={"ordering": ["created_at"]},
        ),
    ]
