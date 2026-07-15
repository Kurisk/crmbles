from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_default_task_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="is_pinned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="is_pinned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="task",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="task",
            options={"ordering": ["-is_pinned", "-pinned_at", "due_date", "created_at"]},
        ),
    ]
