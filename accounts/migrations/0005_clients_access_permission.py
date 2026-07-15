from django.db import migrations, models


def copy_vendor_access_to_clients(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    BusinessMembership = apps.get_model("accounts", "BusinessMembership")

    UserProfile.objects.filter(can_access_vendors=True).update(can_access_clients=True)
    BusinessMembership.objects.filter(can_access_vendors=True).update(can_access_clients=True)


def clear_clients_access(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    BusinessMembership = apps.get_model("accounts", "BusinessMembership")

    UserProfile.objects.update(can_access_clients=False)
    BusinessMembership.objects.update(can_access_clients=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_business_pins"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="can_access_clients",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="businessmembership",
            name="can_access_clients",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(copy_vendor_access_to_clients, clear_clients_access),
    ]
