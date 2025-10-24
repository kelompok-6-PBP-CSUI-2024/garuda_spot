# accounts/tests.py
from __future__ import annotations
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse

User = get_user_model()


class AccountsViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="p", role="USER")

    def test_is_admin_property(self):
        u = User.objects.create_user(username="u1", password="p", role="USER")
        a = User.objects.create_user(username="u2", password="p", role="ADMIN")
        self.assertFalse(u.is_admin)
        self.assertTrue(a.is_admin)

    def test_register_get_ok(self):
        resp = self.client.get(reverse("accounts:register"))
        self.assertEqual(resp.status_code, 200)

    def test_register_post_creates_user_and_redirects_with_message(self):
        resp = self.client.post(
            reverse("accounts:register"),
            {"username": "newu", "password1": "s3cretpassWORD!", "password2": "s3cretpassWORD!"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(username="newu").exists())
        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("Akun berhasil dibuat" in m for m in msgs))

    def test_login_get_ok(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)

    def test_login_post_success_redirects_to_main(self):
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "user", "password": "p"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], reverse("news:show_main"))

    def test_login_post_success_respects_next(self):
        next_url = reverse("accounts:register")
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "user", "password": "p", "next": next_url},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], next_url)

    def test_login_already_authenticated_redirects(self):
        self.client.login(username="user", password="p")
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], reverse("news:show_main"))

    def test_login_invalid_credentials_stays_on_page(self):
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "user", "password": "wrong"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_logout_redirects_to_main(self):
        self.client.login(username="user", password="p")
        resp = self.client.post(reverse("accounts:logout"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], reverse("news:show_main"))
