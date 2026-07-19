from django.db import migrations


def lowercase_existing_usernames(apps, schema_editor):
    User = apps.get_model("auth", "User")
    claimed = set()

    for user in User.objects.order_by("id"):
        base = (user.username or "").strip().lower()
        if not base:
            continue

        candidate = base
        if candidate in claimed:
            suffix = f"-{user.pk}"
            candidate = f"{base[:150 - len(suffix)]}{suffix}"
            counter = 2
            while candidate in claimed:
                numbered_suffix = f"-{user.pk}-{counter}"
                candidate = f"{base[:150 - len(numbered_suffix)]}{numbered_suffix}"
                counter += 1

        claimed.add(candidate)
        if user.username != candidate:
            user.username = candidate
            user.save(update_fields=["username"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_clients_access_permission"),
    ]

    operations = [
        migrations.RunPython(lowercase_existing_usernames, migrations.RunPython.noop),
    ]
