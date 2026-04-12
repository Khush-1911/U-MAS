from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("student_management_app", "0011_merge_20260408_1651"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationstudent",
            name="is_read",
            field=models.BooleanField(default=False),
        ),
    ]
