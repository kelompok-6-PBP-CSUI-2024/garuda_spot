from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from .models import Merch
from . import views
import json

TEMPLATE_DICT = {
    "merch_main.html": "{% for m in list_merch %}{{ m.name }}|{% endfor %}",
    "merch_detail.html": "{{ merch.name }} (views={{ merch.view_count }})",
}

@override_settings(
    TEMPLATES=[{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [("django.template.loaders.locmem.Loader", TEMPLATE_DICT)]
        },
    }]
)
class MerchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.m1 = Merch.objects.create(
            name="Alpha Cap", vendor="A", price=100, stock=5,
            description="Cap desc", thumbnail="", category="cap", link="", view_count=0
        )
        self.m2 = Merch.objects.create(
            name="Beta Jersey", vendor="B", price=200, stock=3,
            description="Jersey desc", thumbnail="", category="jersey", link="", view_count=2
        )
        self.m3 = Merch.objects.create(
            name="Gamma Hoodie", vendor="C", price=150, stock=7,
            description="Hoodie desc", thumbnail="", category="hoodie", link="", view_count=1
        )
        UserModel = get_user_model()
        self.user = UserModel.objects.create_user(
            username="tester", email="tester@example.com", password="pass12345"
        )

    def test_merch_str(self):
        self.assertEqual(str(self.m1), "Alpha Cap")

    def test_to_int_helper(self):
        self.assertEqual(views.to_int("10", 9), 10)
        self.assertEqual(views.to_int("oops", 7), 7)
        self.assertEqual(views.to_int(None, 3), 3)
        self.assertEqual(views.to_int(-5, 0), 0)

    def test_show_merch_filter_and_sort(self):
        resp = self.client.get(reverse("merch:show_merch"), {"filter": "jersey"})
        self.assertEqual(resp.status_code, 200)
        text = resp.content.decode()
        self.assertIn("Beta Jersey", text)
        self.assertNotIn("Alpha Cap", text)
        self.assertNotIn("Gamma Hoodie", text)

        resp = self.client.get(reverse("merch:show_merch"), {"sort": "price_desc"})
        self.assertEqual(resp.status_code, 200)
        parts = [p for p in resp.content.decode().split("|") if p.strip()]
        self.assertEqual(parts, ["Beta Jersey", "Gamma Hoodie", "Alpha Cap"])

    def test_create_merch_requires_login(self):
        resp = self.client.post(reverse("merch:create_merch"), {})
        self.assertIn(resp.status_code, (301, 302))

    def test_create_merch_success_and_validation(self):
        self.client.force_login(self.user)

        resp = self.client.post(reverse("merch:create_merch"), {"vendor": "X"})
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post(reverse("merch:create_merch"), {"name": "Z"})
        self.assertEqual(resp.status_code, 400)

        payload = {
            "name": "Delta Keychain",
            "vendor": "D",
            "description": "desc",
            "thumbnail": "https://x/y.png",
            "category": "invalid-cat",
            "link": "https://shop/item",
            "price": -999,
            "stock": "-5",
        }
        resp = self.client.post(reverse("merch:create_merch"), payload)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["name"], "Delta Keychain")
        self.assertEqual(data["category"], "others")
        self.assertEqual(data["price"], 0)
        self.assertEqual(data["stock"], 0)
        self.assertTrue(Merch.objects.filter(name="Delta Keychain").exists())

    def test_update_merch_success_and_404(self):
        self.client.force_login(self.user)

        resp = self.client.post(reverse("merch:update_merch", args=[99999]), {"name": "Nope"})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.content)["detail"], "Not found")

        payload = {
            "price": "not-a-number",
            "stock": "-10",
            "category": "invalid",
            "thumbnail": "http://img",
            "link": "http://link",
        }
        resp = self.client.post(reverse("merch:update_merch", args=[self.m2.id]), payload)
        self.assertEqual(resp.status_code, 200)
        self.m2.refresh_from_db()
        self.assertEqual(self.m2.price, 200)
        self.assertEqual(self.m2.stock, 0)
        self.assertEqual(self.m2.category, "jersey")
        self.assertEqual(self.m2.thumbnail, "http://img")
        self.assertEqual(self.m2.link, "http://link")
        data = json.loads(resp.content)
        self.assertEqual(data["price"], 200)
        self.assertEqual(data["stock"], 0)
        self.assertEqual(data["category"], "jersey")

    def test_detail_increments_view_count(self):
        self.client.force_login(self.user)
        before = Merch.objects.get(pk=self.m1.id).view_count
        resp = self.client.get(reverse("merch:detail", args=[self.m1.id]))
        self.assertEqual(resp.status_code, 200)
        self.m1.refresh_from_db()
        self.assertEqual(self.m1.view_count, before + 1)
        self.assertIn("Alpha Cap", resp.content.decode())

    def test_delete_merch_method_and_permissions(self):
        self.client.force_login(self.user)

        resp = self.client.get(reverse("merch:delete_merch", args=[self.m3.id]))
        self.assertEqual(resp.status_code, 405)

        resp = self.client.post(reverse("merch:delete_merch", args=[self.m3.id]))
        self.assertEqual(resp.status_code, 403)

        UserModel = get_user_model()
        original = getattr(UserModel, "is_admin", None)
        try:
            UserModel.is_admin = True
            resp = self.client.post(reverse("merch:delete_merch", args=[self.m3.id]))
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(Merch.objects.filter(pk=self.m3.id).exists())
        finally:
            if original is None and hasattr(UserModel, "is_admin"):
                delattr(UserModel, "is_admin")
            else:
                UserModel.is_admin = original

    def test_show_json(self):
        resp = self.client.get(reverse("merch:show_json"))
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        names = {item["name"] for item in data}
        self.assertTrue({"Alpha Cap", "Beta Jersey", "Gamma Hoodie"}.issubset(names))

    def test_show_json_by_id_not_found_path(self):
        req = self.factory.get("/merch/json/999/")
        with patch("merch.views.Merch.objects.select_related") as mock_sel:
            mock_mgr = MagicMock()
            mock_mgr.get.side_effect = Merch.DoesNotExist
            mock_sel.return_value = mock_mgr
            resp = views.show_json_by_id(req, product_id=999)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.content), {"detail": "Not found"})

    def test_show_json_by_id_success_path(self):
        req = self.factory.get(f"/merch/json/{self.m1.id}/")
        fake = MagicMock()
        fake.id = 123
        fake.name = "Omega Scarf"
        fake.vendor = "V"
        fake.price = 321
        fake.stock = 9
        fake.description = "d"
        fake.thumbnail = "t"
        fake.category = "scarf"
        fake.link = "l"
        fake.user_id = 1
        user_mock = MagicMock()
        user_mock.username = "tester"
        fake.user = user_mock

        with patch("merch.views.Merch.objects.select_related") as mock_sel:
            mock_mgr = MagicMock()
            mock_mgr.get.return_value = fake
            mock_sel.return_value = mock_mgr
            resp = views.show_json_by_id(req, product_id=self.m1.id)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["name"], "Omega Scarf")
        self.assertEqual(data["user_username"], "tester")

    def test_admin_and_apps_import(self):
        import merch.admin as _adm
        from merch.apps import MerchConfig
        self.assertEqual(MerchConfig.name, "merch")