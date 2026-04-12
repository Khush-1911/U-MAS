from django.db import migrations, models


def backfill_notification_sender_names(apps, schema_editor):
    NotificationStudent = apps.get_model("student_management_app", "NotificationStudent")
    NotificationStaffs = apps.get_model("student_management_app", "NotificationStaffs")

    NotificationStudent.objects.filter(sender_name="").update(sender_name="HOD")
    NotificationStaffs.objects.filter(sender_name="").update(sender_name="HOD")


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0012_notification_student_read_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationstudent",
            name="sender_name",
            field=models.CharField(default="HOD", max_length=255),
        ),
        migrations.AddField(
            model_name="notificationstaffs",
            name="sender_name",
            field=models.CharField(default="HOD", max_length=255),
        ),
        migrations.RunPython(backfill_notification_sender_names, migrations.RunPython.noop),
    ]
