import io

from openpyxl import Workbook
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from student_management_app.models import Courses, CustomUser, SemesterModel


class StaffStudentImportTests(TestCase):
    def setUp(self):
        self.course = Courses.objects.create(course_name="BCA")
        self.semester = SemesterModel.object.create(
            semester_start_date="2026-01-01",
            semester_end_date="2026-06-30",
        )
        self.staff_user = CustomUser.objects.create_user(
            username="staff_import",
            email="staff_import@example.com",
            password="pass12345",
            user_type=2,
        )
        self.client.force_login(self.staff_user)

    def test_csv_import_creates_unassigned_students(self):
        csv_content = "\n".join(
            [
                "first_name,last_name,username,email,password,address,gender,department,semester_start_date,semester_end_date",
                "Asha,Patel,asha.patel,asha@example.com,pass12345,Ahmedabad,Female,BCA,2026-01-01,2026-06-30",
            ]
        )
        upload = SimpleUploadedFile("students.csv", csv_content.encode("utf-8"), content_type="text/csv")

        response = self.client.post(reverse("staff_import_students_save"), data={"student_file": upload}, follow=True)

        self.assertEqual(response.status_code, 200)
        created_user = CustomUser.objects.get(username="asha.patel")
        self.assertIsNone(created_user.students.assigned_staff)
        self.assertEqual(created_user.students.course_id, self.course)
        self.assertEqual(created_user.students.semester_id, self.semester)

    def test_xlsx_import_skips_duplicate_username(self):
        CustomUser.objects.create_user(
            username="duplicate.student",
            email="existing@example.com",
            password="pass12345",
            user_type=3,
        )

        workbook = Workbook()
        sheet = workbook.active
        sheet.append(
            [
                "first_name",
                "last_name",
                "username",
                "email",
                "password",
                "address",
                "gender",
                "department",
                "semester_start_date",
                "semester_end_date",
            ]
        )
        sheet.append(
            [
                "Ravi",
                "Kumar",
                "duplicate.student",
                "ravi@example.com",
                "pass12345",
                "Surat",
                "Male",
                "BCA",
                "2026-01-01",
                "2026-06-30",
            ]
        )
        buffer = io.BytesIO()
        workbook.save(buffer)
        upload = SimpleUploadedFile(
            "students.xlsx",
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.post(reverse("staff_import_students_save"), data={"student_file": upload}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(username="duplicate.student").count(), 1)
