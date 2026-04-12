from django.db import migrations, models
import django.db.models.deletion


def backfill_student_feedback_routing(apps, schema_editor):
    FeedBackStudent = apps.get_model("student_management_app", "FeedBackStudent")

    for feedback in FeedBackStudent.objects.select_related("student_id", "student_id__assigned_staff"):
        assigned_staff = getattr(feedback.student_id, "assigned_staff", None)
        existing_reply = (feedback.feedback_reply or "").strip()

        feedback.staff_id = assigned_staff
        feedback.forwarded_to_hod = True
        feedback.forwarded_at = feedback.created_at

        if existing_reply:
            feedback.hod_reply = existing_reply
            feedback.feedback_reply = ""

        feedback.save(
            update_fields=[
                "staff_id",
                "forwarded_to_hod",
                "forwarded_at",
                "hod_reply",
                "feedback_reply",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0008_alter_customuser_options_adminhod_profile_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedbackstudent",
            name="forwarded_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="feedbackstudent",
            name="forwarded_to_hod",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="feedbackstudent",
            name="hod_reply",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="feedbackstudent",
            name="staff_id",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="student_feedback_messages",
                to="student_management_app.staffs",
            ),
        ),
        migrations.AlterField(
            model_name="feedbackstudent",
            name="feedback_reply",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(backfill_student_feedback_routing, migrations.RunPython.noop),
    ]
