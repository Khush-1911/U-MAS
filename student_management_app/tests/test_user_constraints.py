import json

from django.db import IntegrityError
from django.test import TestCase

from student_management_app.models import Courses, CustomUser, SessionYearModel, Subjects


class UserConstraintTests(TestCase):
    def setUp(self):
        self.session = SessionYearModel.object.create(
            session_start_year="2025-01-01",
            session_end_year="2025-12-31",
        )
        self.course = Courses.objects.create(course_name="BCA")

        self.staff_user = CustomUser.objects.create_user(
            username="staff_primary",
            email="staff_primary@example.com",
            password="pass12345",
            user_type=2,
        )
        self.other_staff_user = CustomUser.objects.create_user(
            username="staff_secondary",
            email="staff_secondary@example.com",
            password="pass12345",
            user_type=2,
        )

        self.subject = Subjects.objects.create(
            subject_name="Algorithms",
            course_id=self.course,
            staff_id=self.staff_user,
        )

        self.student_user = CustomUser.objects.create_user(
            username="student_primary",
            email="student_primary@example.com",
            password="pass12345",
            user_type=3,
        )
        self.student_user.students.course_id = self.course
        self.student_user.students.session_year_id = self.session
        self.student_user.students.assigned_staff = self.staff_user.staffs
        self.student_user.students.save()

    def test_email_is_unique_case_insensitive_across_roles(self):
        CustomUser.objects.create_user(
            username="hod_case",
            email="CaseCheck@Example.com",
            password="pass12345",
            user_type=1,
        )

        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                username="staff_case",
                email="casecheck@example.com",
                password="pass12345",
                user_type=2,
            )

    def test_role_profile_ids_generated(self):
        hod_user = CustomUser.objects.create_user(
            username="hod_profile",
            email="hod_profile@example.com",
            password="pass12345",
            user_type=1,
        )

        self.assertTrue(hod_user.adminhod.profile_id.startswith("HOD"))
        self.assertTrue(self.staff_user.staffs.profile_id.startswith("STF"))
        self.assertTrue(self.student_user.students.profile_id.startswith("STD"))

    def test_staff_can_fetch_only_assigned_students(self):
        unassigned_for_this_staff = CustomUser.objects.create_user(
            username="student_secondary",
            email="student_secondary@example.com",
            password="pass12345",
            user_type=3,
        )
        unassigned_for_this_staff.students.course_id = self.course
        unassigned_for_this_staff.students.session_year_id = self.session
        unassigned_for_this_staff.students.assigned_staff = self.other_staff_user.staffs
        unassigned_for_this_staff.students.save()

        self.client.force_login(self.staff_user)
        response = self.client.post(
            "/get_students",
            data={"subject": self.subject.id, "session_year": self.session.id},
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode())
        if isinstance(payload, str):
            payload = json.loads(payload)

        returned_admin_ids = {row["id"] for row in payload}
        self.assertIn(self.student_user.id, returned_admin_ids)
        self.assertNotIn(unassigned_for_this_staff.id, returned_admin_ids)

    def test_staff_cannot_fetch_students_for_other_staff_subject(self):
        self.client.force_login(self.other_staff_user)
        response = self.client.post(
            "/get_students",
            data={"subject": self.subject.id, "session_year": self.session.id},
        )
        self.assertEqual(response.status_code, 403)
