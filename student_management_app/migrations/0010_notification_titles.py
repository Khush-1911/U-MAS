from django.db import migrations, models


def backfill_notification_titles(apps, schema_editor):
    NotificationStudent = apps.get_model("student_management_app", "NotificationStudent")
    NotificationStaffs = apps.get_model("student_management_app", "NotificationStaffs")

    NotificationStudent.objects.filter(title="").update(title="Notification")
    NotificationStaffs.objects.filter(title="").update(title="Notification")


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0009_student_feedback_routing"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationstudent",
            name="title",
            field=models.CharField(default="Notification", max_length=255),
        ),
        migrations.AddField(
            model_name="notificationstaffs",
            name="title",
            field=models.CharField(default="Notification", max_length=255),
        ),
        migrations.RunPython(backfill_notification_titles, migrations.RunPython.noop),
    ]
