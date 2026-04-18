from django.db import migrations, models


def backfill_notification_email(apps, schema_editor):
    CustomUser = apps.get_model("student_management_app", "CustomUser")
    for user in CustomUser.objects.all().iterator():
        email = (user.email or "").strip().lower()
        notification_email = (user.notification_email or "").strip().lower()
        if email and not notification_email:
            user.notification_email = email
            user.save(update_fields=["notification_email"])


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0014_semester_refactor"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="notification_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.RunPython(
            backfill_notification_email,
            migrations.RunPython.noop,
        ),
    ]
