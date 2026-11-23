from django.test import TestCase, Client
from django.urls import reverse
from student_management_app.models import CustomUser, Students, Staffs, HOD, Department, Institution
from student_management_app.demo_data_loader import load_demo_data

class DemoDataLoaderTests(TestCase):
    def test_load_demo_data_populates_all_models(self):
        summary = load_demo_data()
        self.assertEqual(summary["institutions"], 1)
        self.assertEqual(summary["semesters"], 1)
        self.assertEqual(summary["departments"], 4)
        self.assertEqual(summary["classes"], 4)
        self.assertEqual(summary["users"], 34)
        self.assertEqual(summary["hods"], 4)
        self.assertEqual(summary["staffs"], 10)
        self.assertEqual(summary["subjects"], 12)
        self.assertEqual(summary["students"], 19)

        # Check owner login
        owner = CustomUser.objects.get(email="siddhpurakhush@umas.com")
        self.assertTrue(owner.check_password("umas@123"))
        self.assertEqual(str(owner.user_type), "1")

        # Check HOD login
        hod_cse = CustomUser.objects.get(email="hod.cse@umas.edu")
        self.assertTrue(hod_cse.check_password("umas@123"))
        self.assertEqual(str(hod_cse.user_type), "7")

    def test_load_demo_data_view_returns_200_and_renders_html(self):
        client = Client()
        response = client.get(reverse("load_demo_data_1519"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo Data Successfully Uploaded")
        self.assertContains(response, "siddhpurakhush@umas.com")
        self.assertContains(response, "umas@123")

    def test_legacy_url_alias_works(self):
        client = Client()
        response = client.get(reverse("create_secret_owners_1519"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo Data Successfully Uploaded")
