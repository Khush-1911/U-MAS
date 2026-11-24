from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from student_management_app.models import (
    ClassModel,
    CustomUser,
    Department,
    HOD,
    Institution,
    NotificationHOD,
    NotificationStaffs,
    NotificationStudent,
    SemesterModel,
    Staffs,
    Students,
    Subjects,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class DepartmentHodNotificationTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Apex University",
            address="123 Campus Road",
            contact_email="contact@apex.edu",
        )
        self.department_cse = Department.objects.create(
            department_name="Computer Science and Engineering",
            institution=self.institution,
        )
        self.department_ece = Department.objects.create(
            department_name="Electronics and Communication Engineering",
            institution=self.institution,
        )
        self.semester = SemesterModel.objects.create(
            semester_start_date="2026-01-01",
            semester_end_date="2026-12-31",
        )

        # Classes
        self.class_cse = ClassModel.objects.create(
            class_name="B.Tech CSE - Sem 1",
            department=self.department_cse,
            semester=self.semester,
            total_students=1,
        )
        self.class_ece = ClassModel.objects.create(
            class_name="B.Tech ECE - Sem 1",
            department=self.department_ece,
            semester=self.semester,
            total_students=1,
        )

        # HOD CSE (User 7)
        self.hod_cse_user = CustomUser.objects.create_user(
            username="hod_cse",
            email="hod_cse@example.com",
            password="pass12345",
            user_type=7,
            first_name="Alan",
            last_name="Turing",
        )
        self.hod_cse_profile = self.hod_cse_user.hod
        self.hod_cse_profile.department = self.department_cse
        self.hod_cse_profile.save()

        # HOD ECE (User 7)
        self.hod_ece_user = CustomUser.objects.create_user(
            username="hod_ece",
            email="hod_ece@example.com",
            password="pass12345",
            user_type=7,
            first_name="Claude",
            last_name="Shannon",
        )
        self.hod_ece_profile = self.hod_ece_user.hod
        self.hod_ece_profile.department = self.department_ece
        self.hod_ece_profile.save()

        # Staff in CSE
        self.staff_cse_user = CustomUser.objects.create_user(
            username="staff_cse",
            email="staff_cse@example.com",
            password="pass12345",
            user_type=2,
            first_name="Grace",
            last_name="Hopper",
        )
        Subjects.objects.create(
            subject_name="Compilers",
            class_id=self.class_cse,
            staff_id=self.staff_cse_user,
        )

        # Student in CSE
        self.student_cse_user = CustomUser.objects.create_user(
            username="student_cse",
            email="student_cse@example.com",
            password="pass12345",
            user_type=3,
            first_name="Ada",
            last_name="Lovelace",
        )
        self.student_cse = self.student_cse_user.students
        self.student_cse.class_id = self.class_cse
        self.student_cse.semester_id = self.semester
        self.student_cse.save()

        # Staff in ECE
        self.staff_ece_user = CustomUser.objects.create_user(
            username="staff_ece",
            email="staff_ece@example.com",
            password="pass12345",
            user_type=2,
            first_name="Nikola",
            last_name="Tesla",
        )
        Subjects.objects.create(
            subject_name="Circuits",
            class_id=self.class_ece,
            staff_id=self.staff_ece_user,
        )

        # Student in ECE
        self.student_ece_user = CustomUser.objects.create_user(
            username="student_ece",
            email="student_ece@example.com",
            password="pass12345",
            user_type=3,
            first_name="Michael",
            last_name="Faraday",
        )
        self.student_ece = self.student_ece_user.students
        self.student_ece.class_id = self.class_ece
        self.student_ece.semester_id = self.semester
        self.student_ece.save()

        self.client.force_login(self.hod_cse_user)

    def test_hod_send_notification_page_loads(self):
        response = self.client.get(reverse("department_hod_send_notification"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification Dispatcher")
        self.assertContains(response, "Computer Science and Engineering")
        self.assertContains(response, "Grace Hopper")
        self.assertContains(response, "Ada Lovelace")
        self.assertContains(response, "Claude Shannon")

    def test_hod_send_notification_to_department_staff(self):
        response = self.client.post(
            reverse("department_hod_send_notification_save"),
            data={
                "title": "CSE Faculty Meeting",
                "message": "Discussion on syllabus updates.",
                "target_group": "staff",
                "staff_ids": [str(self.staff_cse_user.staffs.id)],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 1)
        self.assertEqual(NotificationStudent.objects.count(), 0)
        self.assertEqual(NotificationHOD.objects.count(), 0)

        notif = NotificationStaffs.objects.first()
        self.assertEqual(notif.staff_id, self.staff_cse_user.staffs)
        self.assertEqual(notif.title, "CSE Faculty Meeting")
        self.assertIn("Alan Turing", notif.sender_name)
        self.assertFalse(notif.is_read)

    def test_hod_send_notification_to_department_students(self):
        response = self.client.post(
            reverse("department_hod_send_notification_save"),
            data={
                "title": "CSE Lab Assignment Due",
                "message": "Submit compiler lab report by Friday.",
                "target_group": "student",
                "class_id": "all",
                "student_ids": [str(self.student_cse.id)],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 0)
        self.assertEqual(NotificationStudent.objects.count(), 1)
        self.assertEqual(NotificationHOD.objects.count(), 0)

        notif = NotificationStudent.objects.first()
        self.assertEqual(notif.student_id, self.student_cse)
        self.assertEqual(notif.title, "CSE Lab Assignment Due")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.student_cse_user.email])

    def test_hod_send_notification_to_other_hods(self):
        response = self.client.post(
            reverse("department_hod_send_notification_save"),
            data={
                "title": "Inter-Department Curriculum Review",
                "message": "Inviting all HODs to joint symposium.",
                "target_group": "other_hods",
                "hod_ids": [str(self.hod_ece_profile.id)],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 0)
        self.assertEqual(NotificationStudent.objects.count(), 0)
        self.assertEqual(NotificationHOD.objects.count(), 1)

        notif = NotificationHOD.objects.first()
        self.assertEqual(notif.hod_id, self.hod_ece_profile)
        self.assertEqual(notif.title, "Inter-Department Curriculum Review")
        self.assertIn("HOD - Computer Science", notif.sender_name)
        self.assertFalse(notif.is_read)

    def test_hod_send_notification_to_everyone(self):
        response = self.client.post(
            reverse("department_hod_send_notification_save"),
            data={
                "title": "Annual University Tech Fest",
                "message": "Registration open for all departments.",
                "target_group": "all",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationStaffs.objects.count(), 1)
        self.assertEqual(NotificationStudent.objects.count(), 1)
        self.assertEqual(NotificationHOD.objects.count(), 1)

    def test_hod_view_notification_center_and_mark_read(self):
        # Create a notification directed to HOD CSE
        notif = NotificationHOD.objects.create(
            hod_id=self.hod_cse_profile,
            sender_name="Claude Shannon (HOD - ECE)",
            title="Joint Seminar Invitation",
            message="Please attend our IoT workshop.",
            is_read=False,
        )

        response = self.client.get(reverse("department_hod_notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification Center")
        self.assertContains(response, "Joint Seminar Invitation")
        self.assertContains(response, "Claude Shannon")
        self.assertContains(response, "Unread")

        # Mark single as read
        mark_res = self.client.post(
            reverse("department_hod_notification_mark_read", args=[notif.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(mark_res.status_code, 200)
        self.assertTrue(mark_res.json()["ok"])
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_staff_view_notification_and_mark_read(self):
        self.client.force_login(self.staff_cse_user)
        notif = NotificationStaffs.objects.create(
            staff_id=self.staff_cse_user.staffs,
            sender_name="Alan Turing (HOD - CSE)",
            title="Faculty Review Notice",
            message="Faculty evaluation reports are due next Monday.",
            is_read=False,
        )

        response = self.client.get(reverse("staff_all_notification"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification Center")
        self.assertContains(response, "Faculty Review Notice")
        self.assertContains(response, "Alan Turing")

        # Mark read
        mark_res = self.client.post(
            reverse("staff_notification_mark_read", args=[notif.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(mark_res.status_code, 200)
        self.assertTrue(mark_res.json()["ok"])
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
