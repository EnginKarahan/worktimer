from django.db import migrations


def migrate_roles_forward(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    UserRole = apps.get_model("accounts", "UserRole")
    for profile in UserProfile.objects.select_related("user").all():
        role = getattr(profile, "role", "EMPLOYEE") or "EMPLOYEE"
        UserRole.objects.get_or_create(user=profile.user, role=role)
        # HR and ADMIN always also get EMPLOYEE role
        if role in ("HR", "ADMIN"):
            UserRole.objects.get_or_create(user=profile.user, role="EMPLOYEE")


def migrate_roles_backward(apps, schema_editor):
    UserRole = apps.get_model("accounts", "UserRole")
    UserRole.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_userrole"),
    ]

    operations = [
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),
    ]
