from django.test import TestCase

from student_management_app.models import Department, SemesterModel, Subjects
from student_management_app.models import CustomUser
from student_management_app.services.live_class_service import create_or_get_active_room, end_room


class LiveClassLifecycleTests(TestCase):
    def setUp(self):
        self.semester = SemesterModel.object.create(
            semester_start_date="2025-01-01",
            semester_end_date="2025-12-31",
        )
        self.department = Department.objects.create(department_name="BSc")
        self.staff_user = CustomUser.objects.create_user(
            username="staff_lifecycle",
            email="staff_lifecycle@example.com",
            password="pass12345",
            user_type=2,
        )
        self.subject = Subjects.objects.create(
            subject_name="Math",
            department_id=self.department,
            staff_id=self.staff_user,
        )

    def test_end_room_marks_inactive(self):
        room = create_or_get_active_room(self.staff_user, self.subject.id, self.semester.id)
        end_room(self.staff_user, room)
        room.refresh_from_db()
        self.assertEqual(room.status, "ENDED")
        self.assertFalse(room.is_active)
        self.assertIsNotNone(room.ended_at)
