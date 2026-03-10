from django.test import TestCase

from student_management_app.models import Courses, SessionYearModel, Subjects
from student_management_app.models import CustomUser
from student_management_app.services.live_class_service import create_or_get_active_room, end_room


class LiveClassLifecycleTests(TestCase):
    def setUp(self):
        self.session = SessionYearModel.object.create(
            session_start_year="2025-01-01",
            session_end_year="2025-12-31",
        )
        self.course = Courses.objects.create(course_name="BSc")
        self.staff_user = CustomUser.objects.create_user(
            username="staff_lifecycle",
            email="staff_lifecycle@example.com",
            password="pass12345",
            user_type=2,
        )
        self.subject = Subjects.objects.create(
            subject_name="Math",
            course_id=self.course,
            staff_id=self.staff_user,
        )

    def test_end_room_marks_inactive(self):
        room = create_or_get_active_room(self.staff_user, self.subject.id, self.session.id)
        end_room(self.staff_user, room)
        room.refresh_from_db()
        self.assertEqual(room.status, "ENDED")
        self.assertFalse(room.is_active)
        self.assertIsNotNone(room.ended_at)
