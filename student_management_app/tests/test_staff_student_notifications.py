from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from student_management_app.models import Courses, CustomUser, NotificationStudent, SemesterModel


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class StaffStudentNotificationTests(TestCase):
    def setUp(self):
        self.course = Courses.objects.create(course_name="Computer Science")
        self.semester = SemesterModel.object.create(
            semester_start_date="2026-01-01",
            semester_end_date="2026-12-31",
        )

        self.staff_user = CustomUser.objects.create_user(
            username="staff_scope",
            email="staff_scope@example.com",
            password="pass12345",
            user_type=2,
            first_name="Casey",
            last_name="Staff",
        )
        self.other_staff_user = CustomUser.objects.create_user(
            username="other_staff_scope",
            email="other_staff_scope@example.com",
            password="pass12345",
            user_type=2,
        )

        self.assigned_student_user = CustomUser.objects.create_user(
            username="assigned_student",
            email="assigned_student@example.com",
            password="pass12345",
            user_type=3,
        )
        self.assigned_student_user.students.course_id = self.course
        self.assigned_student_user.students.semester_id = self.semester
        self.assigned_student_user.students.assigned_staff = self.staff_user.staffs
        self.assigned_student_user.students.save()

        self.unassigned_student_user = CustomUser.objects.create_user(
            username="unassigned_student",
            email="unassigned_student@example.com",
            password="pass12345",
            user_type=3,
        )
        self.unassigned_student_user.students.course_id = self.course
        self.unassigned_student_user.students.semester_id = self.semester
        self.unassigned_student_user.students.assigned_staff = self.other_staff_user.staffs
        self.unassigned_student_user.students.save()

        self.client.force_login(self.staff_user)

    def test_staff_can_notify_only_assigned_students(self):
        self.assigned_student_user.notification_email = "assigned_notify@example.com"
        self.assigned_student_user.save(update_fields=["notification_email"])

        response = self.client.post(
            reverse("staff_send_student_notification"),
            data={
                "title": "Mentor Update",
                "message": "Please check the portal.",
                "student_ids": [str(self.assigned_student_user.students.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStudent.objects.count(), 1)
        notification = NotificationStudent.objects.first()
        self.assertEqual(notification.student_id_id, self.assigned_student_user.students.id)
        self.assertEqual(notification.sender_name, "Casey Staff")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["assigned_notify@example.com"])

    def test_staff_cannot_notify_students_outside_assignment(self):
        response = self.client.post(
            reverse("staff_send_student_notification"),
            data={
                "title": "Mentor Update",
                "message": "Please check the portal.",
                "student_ids": [str(self.unassigned_student_user.students.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStudent.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
