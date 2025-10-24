# forum/tests.py
from __future__ import annotations
import os
from uuid import uuid4
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import Category, Post, Comment
from . import views


class ForumTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()

        self.user = User.objects.create_user(username="user", password="p", role="USER")

        mig_admin_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
        mig_admin_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123")
        try:
            self.admin = User.objects.get(username=mig_admin_username)
            self.admin_password = mig_admin_password
        except User.DoesNotExist:
            unique_admin = f"admin_{uuid4().hex[:6]}"
            self.admin = User.objects.create_superuser(username=unique_admin, email="a@a.com", password="p")
            self.admin_password = "p"

        Category.objects.all().delete()
        self.cat_news = Category.objects.create(name="News", slug="news")
        self.cat_player = Category.objects.create(name="Player", slug="player")

        self.p1 = Post.objects.create(
            title="Post 1", slug="post-1", category=self.cat_news, body="hello world", status=Post.PUBLISHED
        )
        self.p2 = Post.objects.create(
            title="Post 2", slug="post-2", category=self.cat_player, body="second body", status=Post.PUBLISHED
        )

    def test_ensure_default_categories_creates_when_empty(self):
        Post.objects.all().delete()
        Category.objects.all().delete()
        views.ensure_default_categories()
        self.assertGreaterEqual(Category.objects.count(), 5)

    @patch("forum.views.render_to_string", return_value="<div>card</div>")
    def test_post_list_partial_paginates_and_filters(self, _mock_tpl):
        for i in range(7):
            Post.objects.create(
                title=f"Extra {i}",
                slug=f"extra-{i}",
                category=self.cat_news,
                body="body",
                status=Post.PUBLISHED,
            )

        self.client.login(username="user", password="p")
        url = reverse("forum:post_list_partial")

        resp = self.client.get(url, {"page": 1, "category": "news"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("html", data)
        self.assertTrue(data["has_next"])

        resp2 = self.client.get(url, {"page": 2, "category": "news"})
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.json()["has_next"])

        resp3 = self.client.get(url, {"q": "second"})
        self.assertEqual(resp3.status_code, 200)
        self.assertIn("html", resp3.json())

    @patch("forum.views.render_to_string", return_value="<div>card</div>")
    def test_post_create_ok_and_invalid(self, _mock_tpl):
        self.client.login(username="user", password="p")
        url = reverse("forum:post_create")

        resp_bad = self.client.post(url, {"title": "", "category": "", "body": ""})
        self.assertEqual(resp_bad.status_code, 400)

        resp = self.client.post(url, {"title": "New", "category": self.cat_news.id, "body": "B", "author_name": "A"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    @patch("forum.views.render_to_string", return_value="<div>comment</div>")
    def test_comment_create_ok_and_invalid(self, _mock_tpl):
        self.client.login(username="user", password="p")
        url = reverse("forum:comment_create", kwargs={"slug": self.p1.slug})

        resp_bad = self.client.post(url, {"author_name": "", "body": ""})
        self.assertEqual(resp_bad.status_code, 400)

        resp = self.client.post(url, {"author_name": "Zed", "body": "Nice"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(self.p1.comments.count(), 1)

    def test_post_like_toggle(self):
        self.client.login(username="user", password="p")
        url = reverse("forum:post_like", kwargs={"slug": self.p1.slug})

        resp1 = self.client.post(url)
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertTrue(data1["liked"])
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.like_count, 1)

        resp2 = self.client.post(url)
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertFalse(data2["liked"])
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.like_count, 0)

    def test_delete_comment_permissions_and_method(self):
        c = Comment.objects.create(post=self.p1, author_name="A", body="x")

        self.client.login(username="user", password="p")
        url = reverse("forum:delete_comment", kwargs={"comment_id": c.id})

        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 403)

        resp_forbidden = self.client.post(url)
        self.assertEqual(resp_forbidden.status_code, 403)

        self.client.logout()
        self.client.login(username=self.admin.username, password=self.admin_password)
        resp_ok = self.client.post(url)
        self.assertEqual(resp_ok.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=c.id).exists())

    def test_delete_post_permissions_and_method(self):
        slug = self.p2.slug
        url = reverse("forum:delete_post", kwargs={"slug": slug})

        self.client.login(username="user", password="p")
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 403)

        resp_forbidden = self.client.post(url)
        self.assertEqual(resp_forbidden.status_code, 403)

        self.client.logout()
        self.client.login(username=self.admin.username, password=self.admin_password)
        resp_ok = self.client.post(url)
        self.assertEqual(resp_ok.status_code, 302)
        self.assertFalse(Post.objects.filter(slug=slug).exists())
