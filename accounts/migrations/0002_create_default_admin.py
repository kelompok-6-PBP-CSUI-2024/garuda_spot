from django.db import migrations
import os

def create_default_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")

    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            password=password,
            role="ADMIN",
        )
        if hasattr(user, "is_staff"):
            user.is_staff = True
        if hasattr(user, "is_superuser"):
            user.is_superuser = True
        user.save()

def remove_default_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
    User.objects.filter(username=username).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(create_default_admin, reverse_code=remove_default_admin),
    ]
