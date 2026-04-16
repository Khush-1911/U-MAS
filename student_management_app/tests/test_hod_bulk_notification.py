from django.test import TestCase

from student_management_app.models import (
    Courses,
    CustomUser,
    NotificationStaffs,
    NotificationStudent,
    SemesterModel,
)


class HodBulkNotificationTests(TestCase):
    def setUp(self):
        self.hod = CustomUser.objects.create_user(
            username="hod_notify",
            email="hod_notify@example.com",
            password="pass12345",
            user_type=1,
        )
        self.client.force_login(self.hod)

        self.department_a = Courses.objects.create(course_name="Computer Engineering")
        self.department_b = Courses.objects.create(course_name="Mechanical Engineering")
        self.semester = SemesterModel.object.create(
            semester_start_date="2026-01-01",
            semester_end_date="2026-12-31",
        )

        self.staff_user_1 = CustomUser.objects.create_user(
            username="staff_notify_1",
            email="staff_notify_1@example.com",
            password="pass12345",
            user_type=2,
        )
        self.staff_user_2 = CustomUser.objects.create_user(
            username="staff_notify_2",
            email="staff_notify_2@example.com",
            password="pass12345",
            user_type=2,
        )

        self.student_user_1 = CustomUser.objects.create_user(
            username="student_notify_1",
            email="student_notify_1@example.com",
            password="pass12345",
            user_type=3,
        )
        self.student_user_1.students.course_id = self.department_a
        self.student_user_1.students.semester_id = self.semester
        self.student_user_1.students.save()

        self.student_user_2 = CustomUser.objects.create_user(
            username="student_notify_2",
            email="student_notify_2@example.com",
            password="pass12345",
            user_type=3,
        )
        self.student_user_2.students.course_id = self.department_b
        self.student_user_2.students.semester_id = self.semester
        self.student_user_2.students.save()

    def test_send_bulk_notification_to_selected_staff(self):
        response = self.client.post(
            "/send_bulk_notification",
            data={
                "title": "Staff Update",
                "message": "Staff-only update",
                "target_group": "staff",
                "staff_ids": [str(self.staff_user_1.staffs.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 1)
        self.assertEqual(NotificationStudent.objects.count(), 0)
        self.assertEqual(NotificationStaffs.objects.first().staff_id_id, self.staff_user_1.staffs.id)
        self.assertEqual(NotificationStaffs.objects.first().title, "Staff Update")

    def test_send_bulk_notification_to_department_students(self):
        response = self.client.post(
            "/send_bulk_notification",
            data={
                "title": "Department Alert",
                "message": "Department notice",
                "target_group": "student",
                "department_id": str(self.department_a.id),
                "student_ids": [str(self.student_user_1.students.id)],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 0)
        self.assertEqual(NotificationStudent.objects.count(), 1)
        self.assertEqual(NotificationStudent.objects.first().student_id_id, self.student_user_1.students.id)
        self.assertEqual(NotificationStudent.objects.first().title, "Department Alert")

    def test_send_bulk_notification_to_all(self):
        response = self.client.post(
            "/send_bulk_notification",
            data={
                "title": "General Notice",
                "message": "All users notice",
                "target_group": "all",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 2)
        self.assertEqual(NotificationStudent.objects.count(), 2)
        self.assertEqual(NotificationStaffs.objects.first().title, "General Notice")
        self.assertEqual(NotificationStudent.objects.first().title, "General Notice")

    def test_send_bulk_notification_to_all_departments_students(self):
        response = self.client.post(
            "/send_bulk_notification",
            data={
                "title": "Department Circular",
                "message": "All department students notice",
                "target_group": "student",
                "department_id": "all_departments",
                "student_ids": [
                    str(self.student_user_1.students.id),
                    str(self.student_user_2.students.id),
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 0)
        self.assertEqual(NotificationStudent.objects.count(), 2)
        self.assertEqual(NotificationStudent.objects.first().title, "Department Circular")
