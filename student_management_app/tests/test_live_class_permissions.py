import json

from django.test import TestCase

from student_management_app.models import Courses, SessionYearModel, Subjects
from student_management_app.models import CustomUser
from student_management_app.services.live_class_service import create_or_get_active_room, end_room


class LiveClassPermissionTests(TestCase):
    def setUp(self):
        self.session = SessionYearModel.object.create(
            session_start_year="2025-01-01",
            session_end_year="2025-12-31",
        )
        self.course = Courses.objects.create(course_name="BTech")
        self.staff_user = CustomUser.objects.create_user(
            username="staff_owner",
            email="staff_owner@example.com",
            password="pass12345",
            user_type=2,
        )
        self.other_staff_user = CustomUser.objects.create_user(
            username="staff_other",
            email="staff_other@example.com",
            password="pass12345",
            user_type=2,
        )
        self.student_user = CustomUser.objects.create_user(
            username="student_one",
            email="student_one@example.com",
            password="pass12345",
            user_type=3,
        )
        self.student_user.students.course_id = self.course
        self.student_user.students.session_year_id = self.session
        self.student_user.students.save()

        self.subject = Subjects.objects.create(
            subject_name="Physics",
            course_id=self.course,
            staff_id=self.staff_user,
        )
        self.room = create_or_get_active_room(self.staff_user, self.subject.id, self.session.id)

    def test_join_token_rejects_ended_room(self):
        end_room(self.staff_user, self.room)
        self.client.force_login(self.student_user)
        response = self.client.post(f"/api/live-class/{self.room.id}/join-token")
        self.assertEqual(response.status_code, 403)
        self.assertIn("not active", response.json()["error"].lower())

    def test_snapshot_only_owner_staff_can_save(self):
        self.client.force_login(self.other_staff_user)
        response = self.client.post(
            f"/api/live-class/{self.room.id}/snapshot",
            data=json.dumps({"snapshot": {"ops": []}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
