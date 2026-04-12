from django.test import TestCase

from student_management_app.models import Courses, CustomUser


class CourseNameValidationTests(TestCase):
    def setUp(self):
        self.hod_user = CustomUser.objects.create_user(
            username="hod_course_admin",
            email="hod_course_admin@example.com",
            password="pass12345",
            user_type=1,
        )
        self.client.force_login(self.hod_user)

    def test_add_course_rejects_exact_duplicate_case_insensitive(self):
        Courses.objects.create(course_name="Computer Engineering")

        response = self.client.post(
            "/add_course_save",
            data={"course": "computer engineering"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/add_course/")
        self.assertEqual(
            Courses.objects.filter(course_name__iexact="computer engineering").count(),
            1,
        )

    def test_add_course_rejects_partial_overlap(self):
        Courses.objects.create(course_name="Computer Engineering")

        response = self.client.post(
            "/add_course_save",
            data={"course": "Computer"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/add_course/")
        self.assertEqual(Courses.objects.count(), 1)
