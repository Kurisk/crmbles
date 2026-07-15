from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendors", "0005_vendor_expense_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="is_pinned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vendor",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name="vendor",
            options={"ordering": ["-is_pinned", "-pinned_at", "name"]},
        ),
    ]
