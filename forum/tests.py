from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from forum.models import Category, Post
from django.contrib.auth import get_user_model

class ForumViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat_news = Category.objects.create(name="News", slug="news")
        cls.cat_player = Category.objects.create(name="Player", slug="player")
        for i in range(8):
            Post.objects.create(
            title=f"News {i}", slug=f"news-{i}", category=cls.cat_news,
            body="lorem ipsum", status=Post.PUBLISHED,
            created_at=timezone.now()
        )
        for i in range(3):
            Post.objects.create(
            title=f"Player {i}", slug=f"player-{i}", category=cls.cat_player,
            body="profil pemain", status=Post.PUBLISHED,
            created_at=timezone.now()
    )


def test_main_page_ok(self):
    url = reverse('forum:post_list')
    resp = self.client.get(url)
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, 'FORUM')
    self.assertContains(resp, 'News')


def test_filter_by_category_ajax(self):
    url = reverse('forum:post_list_partial')
    resp = self.client.get(url, {"category": "player"}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    self.assertEqual(resp.status_code, 200)
    data = resp.json()
    self.assertIn('html', data)
    self.assertIn('has_next', data)
    self.assertIn('Player', data['html'])
    self.assertNotIn('News 0', data['html'])


def test_search_ajax(self):
    url = reverse('forum:post_list_partial')
    resp = self.client.get(url, {"q": "News 1"}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    data = resp.json()
    self.assertIn('News 1', data['html'])


def test_pagination_ajax_has_next(self):
    url = reverse('forum:post_list_partial')
    resp = self.client.get(url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    data = resp.json()
    self.assertTrue(data['has_next'])


def test_pagination_ajax_second_page(self):
    url = reverse('forum:post_list_partial')
    resp = self.client.get(url, {"page": 2}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    self.assertEqual(resp.status_code, 200)
    data = resp.json()
    self.assertIn('html', data)


def test_invalid_page_returns_empty_json(self):
    url = reverse('forum:post_list_partial')
    resp = self.client.get(url, {"page": 999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    self.assertEqual(resp.status_code, 200)
    data = resp.json()
    self.assertIn('html', data)
