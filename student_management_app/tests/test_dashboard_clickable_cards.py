from django.test import TestCase, Client
from django.urls import reverse
from student_management_app.models import (
    CustomUser, Institution, Department, HOD, CollegeAdmin, Principal, Staffs, Students, ClassModel, SemesterModel
)
from datetime import date

class DashboardClickableCardsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.institution = Institution.objects.create(
            name="Test Engineering College",
            contact_email="tec@tec.edu",
            address="123 Campus Road"
        )
        self.department = Department.objects.create(
            department_name="Computer Science",
            institution=self.institution
        )
        self.semester = SemesterModel.objects.create(
            semester_start_date=date(2026, 1, 1),
            semester_end_date=date(2026, 6, 30)
        )
        self.class_obj = ClassModel.objects.create(
            class_name="CS-A",
            department=self.department,
            semester=self.semester
        )

    def test_department_hod_dashboard_links(self):
        hod_user = CustomUser.objects.create_user(
            username="hod_cs@tec.edu",
            email="hod_cs@tec.edu",
            password="password123",
            user_type="7",
            institution=self.institution
        )
        hod_user.hod.department = self.department
        hod_user.hod.save()

        self.client.login(username="hod_cs@tec.edu", password="password123")
        response = self.client.get(reverse("department_hod_home"))
        self.assertEqual(response.status_code, 200)

        # Check links exist in HTML
        self.assertContains(response, reverse("department_hod_manage_students"))
        self.assertContains(response, reverse("department_hod_manage_staff"))
        self.assertContains(response, reverse("department_hod_peer_directory"))
        self.assertContains(response, reverse("department_hod_notifications"))

        # Verify target views render successfully
        res_students = self.client.get(reverse("department_hod_manage_students"))
        self.assertEqual(res_students.status_code, 200)
        res_staff = self.client.get(reverse("department_hod_manage_staff"))
        self.assertEqual(res_staff.status_code, 200)
        res_peers = self.client.get(reverse("department_hod_peer_directory"))
        self.assertEqual(res_peers.status_code, 200)
        res_notif = self.client.get(reverse("department_hod_notifications"))
        self.assertEqual(res_notif.status_code, 200)

    def test_college_admin_dashboard_links(self):
        ca_user = CustomUser.objects.create_user(
            username="ca@tec.edu",
            email="ca@tec.edu",
            password="password123",
            user_type="6",
            institution=self.institution
        )

        self.client.login(username="ca@tec.edu", password="password123")
        response = self.client.get(reverse("collegeadmin_home"))
        self.assertEqual(response.status_code, 200)

        # Check links exist in HTML
        self.assertContains(response, reverse("collegeadmin_manage_students"))
        self.assertContains(response, reverse("collegeadmin_manage_staff"))

        # Verify target views render successfully
        res_students = self.client.get(reverse("collegeadmin_manage_students"))
        self.assertEqual(res_students.status_code, 200)
        res_staff = self.client.get(reverse("collegeadmin_manage_staff"))
        self.assertEqual(res_staff.status_code, 200)

    def test_principal_dashboard_links(self):
        principal_user = CustomUser.objects.create_user(
            username="principal@tec.edu",
            email="principal@tec.edu",
            password="password123",
            user_type="5",
            institution=self.institution
        )

        self.client.login(username="principal@tec.edu", password="password123")
        response = self.client.get(reverse("principal_home"))
        self.assertEqual(response.status_code, 200)

        # Check links exist in HTML
        self.assertContains(response, reverse("principal_manage_users") + "?role=3")
        self.assertContains(response, reverse("principal_manage_users") + "?role=2")
        self.assertContains(response, reverse("principal_departments"))

        # Verify target views render successfully
        res_students = self.client.get(reverse("principal_manage_users") + "?role=3")
        self.assertEqual(res_students.status_code, 200)
        res_dept = self.client.get(reverse("principal_departments"))
        self.assertEqual(res_dept.status_code, 200)

    def test_owner_dashboard_links(self):
        owner_user = CustomUser.objects.create_user(
            username="owner@tec.edu",
            email="owner@tec.edu",
            password="password123",
            user_type="1",
            institution=self.institution
        )

        self.client.login(username="owner@tec.edu", password="password123")
        response = self.client.get(reverse("owner_home"))
        self.assertEqual(response.status_code, 200)

        # Check clickable cards links in HTML
        self.assertContains(response, reverse("manage_institutions"))
        self.assertContains(response, reverse("manage_student"))
        self.assertContains(response, reverse("manage_staff"))
        self.assertContains(response, reverse("manage_department"))

    def test_staff_dashboard_links(self):
        staff_user = CustomUser.objects.create_user(
            username="staff@tec.edu",
            email="staff@tec.edu",
            password="password123",
            user_type="2",
            institution=self.institution
        )

        self.client.login(username="staff@tec.edu", password="password123")
        response = self.client.get(reverse("staff_home"))
        self.assertEqual(response.status_code, 200)

        # Check clickable cards links in HTML
        self.assertContains(response, reverse("staff_students_under_me"))
        self.assertContains(response, reverse("staff_take_attendance"))
        self.assertContains(response, reverse("staff_apply_leave"))
        self.assertContains(response, reverse("staff_add_result"))

    def test_student_dashboard_links(self):
        student_user = CustomUser.objects.create_user(
            username="student@tec.edu",
            email="student@tec.edu",
            password="password123",
            user_type="3",
            institution=self.institution
        )
        student_user.students.class_id = self.class_obj
        student_user.students.semester_id = self.semester
        student_user.students.save()

        self.client.login(username="student@tec.edu", password="password123")
        response = self.client.get(reverse("student_home"))
        self.assertEqual(response.status_code, 200)

        # Check clickable cards links in HTML
        self.assertContains(response, reverse("student_view_attendance"))
        self.assertContains(response, reverse("student_view_result"))
