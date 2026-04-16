from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0013_notification_sender_name"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="SessionYearModel",
            new_name="SemesterModel",
        ),
        migrations.RenameField(
            model_name="semestermodel",
            old_name="session_start_year",
            new_name="semester_start_date",
        ),
        migrations.RenameField(
            model_name="semestermodel",
            old_name="session_end_year",
            new_name="semester_end_date",
        ),
        migrations.RenameField(
            model_name="students",
            old_name="session_year_id",
            new_name="semester_id",
        ),
        migrations.RemoveField(
            model_name="students",
            name="profile_pic",
        ),
        migrations.RenameField(
            model_name="attendance",
            old_name="session_year_id",
            new_name="semester_id",
        ),
        migrations.RenameField(
            model_name="onlineclassroom",
            old_name="session_years",
            new_name="semester",
        ),
    ]
