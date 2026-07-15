from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_profile_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="is_pinned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="business",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
