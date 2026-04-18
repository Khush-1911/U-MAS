from django.test import TestCase
from django.urls import reverse

from student_management_app.models import CustomUser


class ImportedStudentPasswordResetTests(TestCase):
    def setUp(self):
        self.hod = CustomUser.objects.create_user(
            username="hod_reset",
            email="hod_reset@example.com",
            password="pass12345",
            user_type=1,
        )
        self.imported_student = CustomUser.objects.create_user(
            username="dhrumil",
            email="dhrumil_reset@example.com",
            password="oldpassword",
            user_type=3,
        )
        self.other_student = CustomUser.objects.create_user(
            username="other_student",
            email="other_student@example.com",
            password="keepme",
            user_type=3,
        )
        self.client.force_login(self.hod)

    def test_reset_imported_student_passwords_updates_only_known_imported_users(self):
        response = self.client.get(reverse("reset_imported_student_passwords"))

        self.assertEqual(response.status_code, 302)
        self.imported_student.refresh_from_db()
        self.other_student.refresh_from_db()
        self.assertTrue(self.imported_student.check_password("pass12345"))
        self.assertTrue(self.other_student.check_password("keepme"))
