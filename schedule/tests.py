from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from schedule.models import NationalTeamSchedule
import uuid
import datetime
import json

User = get_user_model() 


class NationalTeamScheduleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password', role='USER')
        self.admin_user = User.objects.create_user(username='adminuser', password='password', role='ADMIN')

        self.match = NationalTeamSchedule.objects.create(
            id=uuid.uuid4(),
            home_team="Indonesia",
            away_team="Malaysia",
            match_date=timezone.now() + datetime.timedelta(days=1),
            location="Jakarta",
            category="AFF Championship",
            home_score=2,
            away_score=1,
            shots_home=10,
            shots_away=8,
        )

    # --- MODEL TESTS ---
    def test_str_representation(self):
        self.assertIn("Indonesia vs Malaysia", str(self.match))

    def test_category_image_url_aff(self):
        url = self.match.category_image_url
        self.assertIn("ASEAN_Mitsubishi_Electric_Cup_2024_logo.svg", url)

    def test_is_upcoming_property(self):
        self.assertTrue(self.match.is_upcoming)

    # --- VIEW: show_main ---
    def test_show_main_get(self):
        response = self.client.get(reverse('schedule:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'schedule.html')
        self.assertIn('categories', response.context)

    # --- VIEW: show_match ---
    def test_show_match_detail_perhitungan_statistik(self):
        response = self.client.get(reverse('schedule:show_match', args=[self.match.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_detail.html')
        self.assertIn('stats', response.context)
        self.assertTrue(any('Shots' in s['name'] for s in response.context['stats']))


    # --- VIEW: create_match (non-AJAX) ---
    def test_create_match_post_valid(self):
        self.client.login(username='testuser', password='password')
        data = {
            'home_team': 'Indonesia',
            'away_team': 'Thailand',
            'match_date': timezone.now(),
            'location': 'Bali',
            'category': 'World Cup Qualifiers'
        }
        response = self.client.post(reverse('schedule:show_main'), data)
        self.assertIn(response.status_code, [200, 302])

    # --- VIEW: edit_match ---
    def test_edit_match_post_valid(self):
        self.client.login(username='testuser', password='password')
        data = {
            'home_team': 'Indonesia',
            'away_team': 'Vietnam',
            'match_date': timezone.now(),
            'location': 'Jakarta',
            'category': 'FIFA Matchday A'
        }
        response = self.client.post(reverse('schedule:edit_match', args=[self.match.id]), data)
        self.assertIn(response.status_code, [200, 302])

    # --- VIEW: delete_match ---
    def test_delete_match_post_logged_in(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('schedule:delete_match', args=[self.match.id]))
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(NationalTeamSchedule.objects.filter(id=self.match.id).exists())


    def test_show_json_by_id_not_found(self):
        response = self.client.get(reverse('schedule:show_json_by_id', args=[uuid.uuid4()]))
        self.assertIn(response.status_code, [200, 404])

    # --- AJAX CREATE ---
    def test_create_match_ajax_logged_in_valid(self):
        self.client.login(username='testuser', password='password')
        data = {
            "home_team": "Indonesia",
            "away_team": "Thailand",
            "match_date": timezone.now().isoformat(),
            "location": "Jakarta",
            "category": "FIFA Matchday A",
        }
        response = self.client.post(reverse('schedule:add_match_ajax'), data)
        self.assertIn(response.status_code, [200, 201])
        self.assertTrue(b"CREATED" in response.content or b"success" in response.content.lower())

    def test_create_match_ajax_missing_required_field(self):
        self.client.login(username='testuser', password='password')
        data = {"home_team": "", "away_team": ""}
        response = self.client.post(reverse('schedule:add_match_ajax'), data)
        self.assertIn(response.status_code, [400, 422])
        self.assertTrue(b"INVALID" in response.content or b"error" in response.content.lower())

    # --- AJAX UPDATE ---
    def test_update_match_ajax_admin_valid(self):
        self.client.login(username='adminuser', password='password')
        data = {
            "home_team": "Indonesia",
            "away_team": "Singapore",
            "match_date": timezone.now(),
            "location": "Bandung",
            "category": "AFC Cup",
        }
        response = self.client.post(reverse('schedule:update_match_ajax', args=[self.match.id]), data)
        self.assertIn(response.status_code, [200, 201])
        result = json.loads(response.content)
        self.assertIn("Singapore", result.get("away_team", ""))

    def test_update_match_ajax_not_admin(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('schedule:update_match_ajax', args=[self.match.id]), {})
        self.assertEqual(response.status_code, 403)

    # --- AJAX DELETE ---
    def test_delete_match_ajax_admin_valid(self):
        self.client.login(username='adminuser', password='password')
        response = self.client.post(reverse('schedule:delete_match_ajax', args=[self.match.id]))
        self.assertIn(response.status_code, [200, 204])
        self.assertIn(str(self.match.id).encode(), response.content)

    def test_delete_match_ajax_not_admin(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('schedule:delete_match_ajax', args=[self.match.id]))
        self.assertEqual(response.status_code, 403)
