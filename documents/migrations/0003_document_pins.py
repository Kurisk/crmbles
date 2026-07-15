from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_document_business"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="is_pinned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="document",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="document",
            options={"ordering": ["-is_pinned", "-pinned_at", "-updated_at"]},
        ),
    ]
