from django.test import TestCase
from django.urls import reverse

from student_management_app.models import Courses, CustomUser, NotificationStudent, SessionYearModel


class StudentNotificationTests(TestCase):
    def setUp(self):
        self.course = Courses.objects.create(course_name="BCA")
        self.session = SessionYearModel.object.create(
            session_start_year="2026-01-01",
            session_end_year="2026-12-31",
        )
        self.student_user = CustomUser.objects.create_user(
            username="student_notifications",
            email="student_notifications@example.com",
            password="pass12345",
            user_type=3,
        )
        self.student_user.students.course_id = self.course
        self.student_user.students.session_year_id = self.session
        self.student_user.students.save()

        self.unread_notification = NotificationStudent.objects.create(
            student_id=self.student_user.students,
            sender_name="Dean Office",
            title="Unread Notice",
            message="This is unread",
            is_read=False,
        )
        self.read_notification = NotificationStudent.objects.create(
            student_id=self.student_user.students,
            title="Read Notice",
            message="This is read",
            is_read=True,
        )

        self.client.force_login(self.student_user)

    def test_student_notification_page_shows_badge_and_unread_first(self):
        response = self.client.get(reverse("student_all_notification"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="studentNotificationBadge"', html=False)
        self.assertContains(response, "Unread")
        self.assertContains(response, "Read")
        self.assertContains(response, "New notification from Dean Office")

        content = response.content.decode()
        self.assertLess(content.find("Unread Notice"), content.find("Read Notice"))

    def test_student_can_mark_notification_as_read(self):
        response = self.client.post(
            reverse("student_notification_mark_read", args=[self.unread_notification.id]),
        )

        self.assertEqual(response.status_code, 200)
        self.unread_notification.refresh_from_db()
        self.assertTrue(self.unread_notification.is_read)
        self.assertEqual(response.json()["unread_count"], 0)
