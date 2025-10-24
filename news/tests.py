# news/tests.py
from __future__ import annotations
import json
import os
from datetime import datetime
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory, SimpleTestCase
from django.urls import reverse

from .models import News
from . import views


class UtilsTests(SimpleTestCase):
    def test_extract_month_various_locales(self):
        self.assertEqual(views._extract_month("Kamis, 09 Okt 2025 13:40 WIB"), 10)
        self.assertEqual(views._extract_month("9 October 2025"), 10)
        self.assertEqual(views._extract_month("12 Desember 2024"), 12)
        self.assertEqual(views._extract_month("1 Mei 2023"), 5)
        self.assertEqual(views._extract_month("21 Aug 2022"), 8)
        self.assertIsNone(views._extract_month("July 2025"))

    def test_extract_month_handles_none_or_weird(self):
        self.assertIsNone(views._extract_month(""))
        self.assertIsNone(views._extract_month(None))
        self.assertIsNone(views._extract_month("no date here"))

    def test_parse_dt_accepts_dayname_and_24h(self):
        dt = views._parse_dt_for_sort("Kamis, 09 Okt 2025 13:40 WIB")
        self.assertEqual(dt, datetime(2025, 10, 9, 13, 40))

    def test_parse_dt_accepts_without_dayname_and_time(self):
        dt = views._parse_dt_for_sort("09 Okt 2025")
        self.assertEqual(dt, datetime(2025, 10, 9, 0, 0))

    def test_parse_dt_numeric_month(self):
        dt = views._parse_dt_for_sort("09 10 2025 08:05")
        self.assertEqual(dt, datetime(2025, 10, 9, 8, 5))

    def test_parse_dt_invalid_returns_none(self):
        self.assertIsNone(views._parse_dt_for_sort("Sept 31 2025"))
        self.assertIsNone(views._parse_dt_for_sort("foo bar"))
        self.assertIsNone(views._parse_dt_for_sort(""))


class BaseNewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rf = RequestFactory()
        User = get_user_model()
        News.objects.all().delete()
        self.user = User.objects.create_user(username="user", password="p", role="USER")
        mig_admin_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        mig_admin_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")
        try:
            self.admin = User.objects.get(username=mig_admin_username)
            if getattr(self.admin, "role", None) != "ADMIN":
                self.admin.role = "ADMIN"
                self.admin.save(update_fields=["role"])
            self.admin_username = mig_admin_username
            self.admin_password = mig_admin_password
        except User.DoesNotExist:
            unique_admin_username = f"admin_{uuid4().hex[:6]}"
            self.admin = User.objects.create_user(
                username=unique_admin_username, password="p", role="ADMIN"
            )
            self.admin_username = unique_admin_username
            self.admin_password = "p"
        self.n1 = News.objects.create(
            title="A",
            category="Cat",
            publish_date="09 Okt 2025 13:40",
            published_month=10,
            content="content A",
        )
        self.n2 = News.objects.create(
            title="B",
            category="Cat",
            publish_date="08 Sep 2025 09:00",
            published_month=9,
            content="content B",
        )
        self.n3 = News.objects.create(
            title="C",
            category="Cat",
            publish_date="01 Mei 2024",
            published_month=5,
            content="content C",
        )
        self.n4 = News.objects.create(
            title="D",
            category="Cat",
            publish_date="",
            published_month=None,
            content="content D",
        )


class PublicAndHTMLViewsTests(BaseNewsTestCase):
    def test_show_main(self):
        resp = self.client.get(reverse("news:show_main"))
        self.assertEqual(resp.status_code, 200)

    def test_show_news_requires_login(self):
        url = reverse("news:show_news", kwargs={"id": self.n1.id})
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (302, 301))
        self.client.login(username="user", password="p")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_create_edit_delete_require_admin(self):
        self.client.login(username="user", password="p")
        self.assertEqual(self.client.get(reverse("news:create_news")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("news:edit_news", kwargs={"id": self.n1.id})).status_code, 403
        )
        self.assertEqual(
            self.client.get(reverse("news:delete_news", kwargs={"id": self.n1.id})).status_code, 403
        )
        self.client.logout()
        self.client.login(username=self.admin_username, password=self.admin_password)
        resp = self.client.post(
            reverse("news:create_news"),
            {"title": "New T", "category": "General", "publish_date": "09 Okt 2025", "content": "Body"},
        )
        self.assertEqual(resp.status_code, 302)
        resp = self.client.post(
            reverse("news:edit_news", kwargs={"id": self.n1.id}),
            {"title": "A edited", "category": "Cat", "publish_date": "09 Okt 2025", "content": "content A"},
        )
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get(reverse("news:delete_news", kwargs={"id": self.n1.id}))
        self.assertEqual(resp.status_code, 302)


class APIJSONXMLTests(BaseNewsTestCase):
    def test_show_json_default_desc_sort(self):
        resp = self.client.get(reverse("news:show_json"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 4)
        titles = [it["title"] for it in data["items"]]
        self.assertEqual(titles, ["A", "B", "C", "D"])

    def test_show_json_asc_sort(self):
        resp = self.client.get(reverse("news:show_json") + "?sort=asc")
        self.assertEqual(resp.status_code, 200)
        titles = [it["title"] for it in resp.json()["items"]]
        self.assertEqual(titles, ["D", "C", "B", "A"])

    def test_show_json_month_filter(self):
        resp = self.client.get(reverse("news:show_json") + "?month=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["title"], "A")

    def test_show_json_pagination(self):
        resp = self.client.get(reverse("news:show_json") + "?page_size=2&page=1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["items"]), 2)
        self.assertTrue(data["has_next"])
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 2)
        resp2 = self.client.get(reverse("news:show_json") + "?page_size=2&page=2")
        data2 = resp2.json()
        self.assertEqual(len(data2["items"]), 2)
        self.assertFalse(data2["has_next"])
        self.assertEqual(data2["page"], 2)

    def test_show_json_by_id_ok_and_not_found(self):
        url_ok = reverse("news:show_json_by_id", kwargs={"news_id": self.n1.id})
        resp = self.client.get(url_ok)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["title"], self.n1.title)
        url_nf = reverse("news:show_json_by_id", kwargs={"news_id": uuid4()})
        resp_nf = self.client.get(url_nf)
        self.assertEqual(resp_nf.status_code, 404)
        self.assertIn("detail", resp_nf.json())

    def test_show_xml_and_xml_by_id(self):
        resp = self.client.get(reverse("news:show_xml"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"<object", resp.content)
        resp2 = self.client.get(reverse("news:show_xml_by_id", kwargs={"news_id": self.n2.id}))
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(str(self.n2.id).encode(), resp2.content)


class AJAXEndpointsTests(BaseNewsTestCase):
    def test_add_news_entry_ajax_requires_login_and_admin(self):
        url = reverse("news:add_news_entry_ajax")
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, (302, 301))
        self.client.login(username="user", password="p")
        resp = self.client.post(url, {"title": "X", "category": "C", "content": "Body"})
        self.assertEqual(resp.status_code, 403)
        self.client.logout()
        self.client.login(username=self.admin_username, password=self.admin_password)
        resp = self.client.post(
            url,
            {"title": "X", "category": "C", "publish_date": "01 Okt 2025", "content": "Body"},
        )
        self.assertEqual(resp.status_code, 201)
        payload = json.loads(resp.content.decode())
        self.assertEqual(payload["title"], "X")
        obj_id = payload["id"]
        obj = News.objects.get(pk=obj_id)
        self.assertEqual(obj.published_month, 10)
        resp_bad = self.client.post(url, {"title": "", "category": "", "content": ""})
        self.assertEqual(resp_bad.status_code, 400)

    def test_delete_news_ajax_requires_admin(self):
        url = reverse("news:delete_news_ajax", kwargs={"id": self.n3.id})
        resp = self.client.post(url)
        self.assertIn(resp.status_code, (302, 301))
        self.client.login(username="user", password="p")
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)
        self.client.logout()
        self.client.login(username=self.admin_username, password=self.admin_password)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(News.objects.filter(id=self.n3.id).exists())
