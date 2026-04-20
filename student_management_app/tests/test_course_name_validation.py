from django.test import TestCase

from student_management_app.models import Department, CustomUser


class DepartmentNameValidationTests(TestCase):
    def setUp(self):
        self.hod_user = CustomUser.objects.create_user(
            username="hod_department_admin",
            email="hod_department_admin@example.com",
            password="pass12345",
            user_type=1,
        )
        self.client.force_login(self.hod_user)

    def test_add_department_rejects_exact_duplicate_case_insensitive(self):
        Department.objects.create(department_name="Computer Engineering")

        response = self.client.post(
            "/add_department_save",
            data={"department": "computer engineering"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/add_department/")
        self.assertEqual(
            Department.objects.filter(department_name__iexact="computer engineering").count(),
            1,
        )

    def test_add_department_rejects_partial_overlap(self):
        Department.objects.create(department_name="Computer Engineering")

        response = self.client.post(
            "/add_department_save",
            data={"department": "Computer"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/add_department/")
        self.assertEqual(Department.objects.count(), 1)
