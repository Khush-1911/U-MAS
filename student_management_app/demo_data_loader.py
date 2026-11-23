import os
import json
from django.conf import settings
from django.core import serializers
from django.db import transaction, connection
from django.core.management.color import no_style
from django.db.models.signals import post_save

from student_management_app.models import (
    CustomUser, Institution, SemesterModel, Department, ClassModel,
    OwnerProfile, Principal, CollegeAdmin, HOD, Staffs, Subjects, Students,
    Attendance, AttendanceReport, LeaveReportStaff, LeaveReportStudent,
    FeedBackStaffs, FeedBackStudent, NotificationStaffs, NotificationStudent,
    StudentResult, Timetable, OnlineClassRoom, LiveClassParticipant,
    create_user_profile, save_user_profile
)

CANDIDATE_PATHS = [
    os.path.join(settings.BASE_DIR, "demo_data.json"),
    os.path.join(settings.BASE_DIR, "student_management_app", "fixtures", "demo_data.json"),
    os.path.join(settings.BASE_DIR, "datadump.json"),
]

def find_demo_data_file():
    for path in CANDIDATE_PATHS:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    return None

def load_demo_data(file_path=None):
    target_file = file_path or find_demo_data_file()
    if not target_file or not os.path.exists(target_file):
        raise FileNotFoundError(
            f"Demo data fixture file not found. Checked: {CANDIDATE_PATHS}"
        )

    with open(target_file, "r", encoding="utf-8") as f:
        raw_data = f.read()

    # Disconnect signals to prevent auto-creating empty profiles or colliding with OneToOne fields
    post_save.disconnect(create_user_profile, sender=CustomUser)
    post_save.disconnect(save_user_profile, sender=CustomUser)

    try:
        with transaction.atomic():
            # Delete dependent records in reverse FK order to prevent foreign key errors
            LiveClassParticipant.objects.all().delete()
            OnlineClassRoom.objects.all().delete()
            Timetable.objects.all().delete()
            StudentResult.objects.all().delete()
            NotificationStudent.objects.all().delete()
            NotificationStaffs.objects.all().delete()
            FeedBackStudent.objects.all().delete()
            FeedBackStaffs.objects.all().delete()
            LeaveReportStudent.objects.all().delete()
            LeaveReportStaff.objects.all().delete()
            AttendanceReport.objects.all().delete()
            Attendance.objects.all().delete()
            Students.objects.all().delete()
            Subjects.objects.all().delete()
            Staffs.objects.all().delete()
            HOD.objects.all().delete()
            ClassModel.objects.all().delete()
            Department.objects.all().delete()
            OwnerProfile.objects.all().delete()
            Principal.objects.all().delete()
            CollegeAdmin.objects.all().delete()
            CustomUser.objects.all().delete()
            SemesterModel.objects.all().delete()
            Institution.objects.all().delete()

            # Deserialize and save instances
            loaded_count = 0
            for obj in serializers.deserialize("json", raw_data):
                obj.save()
                loaded_count += 1

            # Reset database sequences (crucial for PostgreSQL on Render)
            models_to_reset = [
                Institution, SemesterModel, Department, ClassModel,
                CustomUser, OwnerProfile, Principal, CollegeAdmin,
                HOD, Staffs, Subjects, Students, Attendance,
                AttendanceReport, LeaveReportStaff, LeaveReportStudent,
                FeedBackStaffs, FeedBackStudent, NotificationStaffs,
                NotificationStudent, StudentResult, Timetable,
                OnlineClassRoom, LiveClassParticipant
            ]
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), models_to_reset)
            if sequence_sql:
                with connection.cursor() as cursor:
                    for sql in sequence_sql:
                        cursor.execute(sql)

            summary = {
                "institutions": Institution.objects.count(),
                "semesters": SemesterModel.objects.count(),
                "departments": Department.objects.count(),
                "classes": ClassModel.objects.count(),
                "users": CustomUser.objects.count(),
                "owner_profiles": OwnerProfile.objects.count(),
                "hods": HOD.objects.count(),
                "staffs": Staffs.objects.count(),
                "subjects": Subjects.objects.count(),
                "students": Students.objects.count(),
                "total_objects_loaded": loaded_count,
            }
            return summary
    finally:
        post_save.connect(create_user_profile, sender=CustomUser)
        post_save.connect(save_user_profile, sender=CustomUser)
