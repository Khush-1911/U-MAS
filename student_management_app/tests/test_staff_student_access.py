from django.test import TestCase, override_settings
from django.urls import reverse

from student_management_app.models import (
    ClassModel,
    CustomUser,
    Department,
    NotificationStudent,
    SemesterModel,
    Subjects,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class StaffStudentAccessTests(TestCase):
    def setUp(self):
        self.semester = SemesterModel.objects.create(
            semester_start_date="2026-07-01",
            semester_end_date="2026-12-20",
        )
        self.cse = Department.objects.create(department_name="Computer Science")
        self.ece = Department.objects.create(department_name="Electronics")
        self.cse_class = ClassModel.objects.create(
            class_name="CSE Semester 1", department=self.cse, semester=self.semester
        )
        self.ece_class = ClassModel.objects.create(
            class_name="ECE Semester 1", department=self.ece, semester=self.semester
        )
        self.staff = CustomUser.objects.create_user(
            username="staff@example.com", email="staff@example.com", password="pass12345", user_type="2"
        )
        self.other_staff = CustomUser.objects.create_user(
            username="other@example.com", email="other@example.com", password="pass12345", user_type="2"
        )
        Subjects.objects.create(
            subject_name="Programming", class_id=self.cse_class, staff_id=self.staff
        )

        self.mentor_student = self._student("mentor@example.com", self.ece_class, self.staff.staffs)
        self.subject_student = self._student("subject@example.com", self.cse_class, self.other_staff.staffs)
        self.other_student = self._student("otherstudent@example.com", self.ece_class, self.other_staff.staffs)

        self.hod = CustomUser.objects.create_user(
            username="hod@example.com", email="hod@example.com", password="pass12345", user_type="7"
        )
        self.hod.hod.department = self.cse
        self.hod.hod.save(update_fields=["department"])

    def _student(self, email, class_obj, mentor):
        user = CustomUser.objects.create_user(
            username=email, email=email, password="pass12345", user_type="3"
        )
        user.students.class_id = class_obj
        user.students.semester_id = self.semester
        user.students.mentor = mentor
        user.students.save()
        return user

    def test_staff_can_view_students_from_mentorship_or_subject_class_only(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("staff_students_under_me"))

        self.assertContains(response, self.mentor_student.email)
        self.assertContains(response, self.subject_student.email)
        self.assertNotContains(response, self.other_student.email)

    def test_staff_can_notify_a_subject_student_but_not_an_unrelated_student(self):
        self.client.force_login(self.staff)

        allowed = self.client.post(
            reverse("staff_send_student_notification"),
            {"title": "Lecture update", "message": "Room 204 at 10 AM.", "student_ids": [self.subject_student.students.id]},
        )
        blocked = self.client.post(
            reverse("staff_send_student_notification"),
            {"title": "Lecture update", "message": "Room 204 at 10 AM.", "student_ids": [self.other_student.students.id]},
        )

        self.assertEqual(allowed.status_code, 302)
        self.assertEqual(blocked.status_code, 302)
        self.assertEqual(NotificationStudent.objects.count(), 1)
        self.assertEqual(NotificationStudent.objects.first().student_id, self.subject_student.students)

    def test_hod_roster_is_limited_to_the_hods_department(self):
        self.client.force_login(self.hod)

        response = self.client.get(reverse("department_hod_manage_students"))

        self.assertContains(response, self.subject_student.email)
        self.assertNotContains(response, self.mentor_student.email)
        self.assertNotContains(response, self.other_student.email)
