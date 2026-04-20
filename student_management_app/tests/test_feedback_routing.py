from django.test import TestCase
from django.urls import reverse

from student_management_app.models import Department, CustomUser, FeedBackStudent, SemesterModel


class FeedbackRoutingTests(TestCase):
    def setUp(self):
        self.semester = SemesterModel.object.create(
            semester_start_date="2025-01-01",
            semester_end_date="2025-12-31",
        )
        self.department = Department.objects.create(department_name="BCA")

        self.hod_user = CustomUser.objects.create_user(
            username="hod_feedback",
            email="hod_feedback@example.com",
            password="pass12345",
            user_type=1,
        )
        self.staff_user = CustomUser.objects.create_user(
            username="staff_feedback",
            email="staff_feedback@example.com",
            password="pass12345",
            user_type=2,
        )
        self.other_staff_user = CustomUser.objects.create_user(
            username="other_staff_feedback",
            email="other_staff_feedback@example.com",
            password="pass12345",
            user_type=2,
        )
        self.student_user = CustomUser.objects.create_user(
            username="student_feedback",
            email="student_feedback@example.com",
            password="pass12345",
            user_type=3,
        )

        self.student_user.students.department_id = self.department
        self.student_user.students.semester_id = self.semester
        self.student_user.students.mentor = self.staff_user.staffs
        self.student_user.students.save()

    def test_student_feedback_is_routed_to_mentor(self):
        self.client.force_login(self.student_user)
        response = self.client.post(
            reverse("student_feedback_save"),
            data={"feedback_msg": "Need help with attendance"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        feedback = FeedBackStudent.objects.get()
        self.assertEqual(feedback.student_id, self.student_user.students)
        self.assertEqual(feedback.staff_id, self.staff_user.staffs)
        self.assertFalse(feedback.forwarded_to_hod)
        self.assertEqual(feedback.feedback_reply, "")
        self.assertEqual(feedback.hod_reply, "")

        self.client.force_login(self.staff_user)
        staff_response = self.client.get(reverse("staff_feedback"))
        self.assertContains(staff_response, "Need help with attendance")

        self.client.force_login(self.other_staff_user)
        other_staff_response = self.client.get(reverse("staff_feedback"))
        self.assertNotContains(other_staff_response, "Need help with attendance")

        self.client.force_login(self.hod_user)
        hod_response = self.client.get(reverse("student_feedback_message"))
        self.assertNotContains(hod_response, "Need help with attendance")

    def test_staff_can_reply_and_forward_student_feedback_to_hod(self):
        feedback = FeedBackStudent.objects.create(
            student_id=self.student_user.students,
            staff_id=self.staff_user.staffs,
            feedback="Project issue",
        )

        self.client.force_login(self.staff_user)
        reply_response = self.client.post(
            reverse("staff_student_feedback_reply"),
            data={"feedback_id": feedback.id, "reply_message": "Please meet me after class"},
            follow=True,
        )
        self.assertEqual(reply_response.status_code, 200)

        feedback.refresh_from_db()
        self.assertEqual(feedback.feedback_reply, "Please meet me after class")
        self.assertFalse(feedback.forwarded_to_hod)

        forward_response = self.client.post(
            reverse("staff_student_feedback_forward"),
            data={"feedback_id": feedback.id},
            follow=True,
        )
        self.assertEqual(forward_response.status_code, 200)

        feedback.refresh_from_db()
        self.assertTrue(feedback.forwarded_to_hod)
        self.assertIsNotNone(feedback.forwarded_at)

        self.client.force_login(self.hod_user)
        hod_response = self.client.get(reverse("student_feedback_message"))
        self.assertContains(hod_response, "Project issue")
        self.assertContains(hod_response, "Please meet me after class")

        reply_to_hod = self.client.post(
            reverse("student_feedback_message_replied"),
            data={"id": feedback.id, "message": "Reviewed by HOD"},
        )
        self.assertEqual(reply_to_hod.status_code, 200)

        feedback.refresh_from_db()
        self.assertEqual(feedback.hod_reply, "Reviewed by HOD")

        self.client.force_login(self.student_user)
        student_response = self.client.get(reverse("student_feedback"))
        self.assertContains(student_response, "Please meet me after class")
        self.assertContains(student_response, "Reviewed by HOD")
