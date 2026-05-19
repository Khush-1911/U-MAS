from django.test import TestCase, override_settings

from student_management_app.models import CustomUser


@override_settings(DEBUG=True)
class LoginFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="login_user",
            email="login_user@example.com",
            password="pass12345",
            user_type=2,
        )

    def test_do_login_authenticates_with_email_backend(self):
        response = self.client.post(
            "/doLogin",
            data={
                "email": self.user.email,
                "password": "pass12345",
                "g-recaptcha-response": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/staff_home")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)
