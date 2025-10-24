from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import User
from .models import TicketMatch, TicketLink


class TicketViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="user",
            password="pass",
            role=User.Roles.USER,
        )

    def login_admin(self):
        if self.client.login(username="root", password="root123"):
            return True
        if self.client.login(username="admin", password="admin123"):
            return True
        UserModel = get_user_model()
        try:
            admin = UserModel.objects.get(username="admin")
            admin.role = User.Roles.ADMIN
            admin.set_password("admin123")
            admin.save()
        except UserModel.DoesNotExist:
            admin = UserModel.objects.create_user(
                username="admin",
                password="admin123",
                role=User.Roles.ADMIN,
            )
        return self.client.login(username="admin", password="admin123")

    def _create_match_payload(self, **overrides):
        base = {
            "team1": "Garuda",
            "team2": "Rival",
            "img_team1": "https://example.com/t1.png",
            "img_team2": "https://example.com/t2.png",
            "img_cup": "https://example.com/cup.png",
            "place": "Stadium",
            "date": timezone.now().date().isoformat(),
        }
        base.update(overrides)
        return base

    def _create_link_payload(self, **overrides):
        base = {
            "vendor": "VendorA",
            "vendor_link": "https://vendor.example.com/ticket",
            "price": 123456,
            "img_vendor": "https://vendor.example.com/logo.png",
        }
        base.update(overrides)
        return base

    def test_non_admin_forbidden_crud(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("tickets:create_ticket"), self._create_match_payload())
        self.assertEqual(r.status_code, 403)
        r = self.client.get(reverse("tickets:form_match"))
        self.assertEqual(r.status_code, 403)

    def test_admin_can_create_edit_delete(self):
        self.assertTrue(self.login_admin())
        r = self.client.post(reverse("tickets:create_ticket"), self._create_match_payload())
        self.assertEqual(r.status_code, 201)
        m = TicketMatch.objects.first()
        self.assertIsNotNone(m)
        r = self.client.post(reverse("tickets:edit_ticket", args=[m.match_id]), self._create_match_payload(team1="GarudaX"))
        self.assertEqual(r.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.team1, "GarudaX")
        r = self.client.post(reverse("tickets:create_link", args=[m.match_id]), self._create_link_payload(price=200000))
        self.assertEqual(r.status_code, 201)
        l = TicketLink.objects.filter(match=m).first()
        self.assertIsNotNone(l)
        r = self.client.post(reverse("tickets:delete_link", args=[l.link_id]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(TicketLink.objects.filter(pk=l.pk).exists())
        r = self.client.post(reverse("tickets:delete_ticket", args=[m.match_id]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(TicketMatch.objects.filter(pk=m.pk).exists())

    def test_json_endpoints(self):
        m = TicketMatch.objects.create(
            team1="A",
            team2="B",
            img_team1="https://example.com/a.png",
            img_team2="https://example.com/b.png",
            img_cup=None,
            place=None,
            date=timezone.now().date(),
        )
        TicketLink.objects.create(
            match=m,
            vendor="V",
            vendor_link="https://v.example.com",
            price=10,
            img_vendor="https://v.example.com/logo.png",
        )
        r = self.client.get(reverse("tickets:show_json"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        r = self.client.get(reverse("tickets:show_json_by_uuid", args=[m.match_id]))
        self.assertEqual(r.status_code, 200)
        obj = r.json()
        self.assertEqual(obj["match_id"], str(m.match_id))
        self.assertIn("links", obj)

    def test_detail_view(self):
        m = TicketMatch.objects.create(
            team1="A",
            team2="B",
            img_team1="https://example.com/a.png",
            img_team2="https://example.com/b.png",
            img_cup=None,
            place=None,
            date=timezone.now().date(),
        )
        r = self.client.get(reverse("tickets:detail", args=[m.match_id]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "A")
        self.assertContains(r, "B")

    def test_admin_can_open_forms_and_xml(self):
        self.assertTrue(self.login_admin())
        r = self.client.get(reverse("tickets:form_match"))
        self.assertEqual(r.status_code, 200)
        r = self.client.post(reverse("tickets:create_ticket"), self._create_match_payload())
        self.assertEqual(r.status_code, 201)
        m = TicketMatch.objects.first()
        r = self.client.get(reverse("tickets:form_link", args=[m.match_id]))
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("tickets:show_xml"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/xml", r.headers.get("Content-Type", ""))
        r = self.client.get(reverse("tickets:show_xml_by_id", args=[m.id]))
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("tickets:show_xml_by_uuid", args=[m.match_id]))
        self.assertEqual(r.status_code, 200)

    def test_invalid_create_returns_400(self):
        self.assertTrue(self.login_admin())
        payload = self._create_match_payload()
        payload.pop("team1")
        r = self.client.post(reverse("tickets:create_ticket"), payload)
        self.assertEqual(r.status_code, 400)
        r = self.client.post(reverse("tickets:create_ticket"), self._create_match_payload())
        self.assertEqual(r.status_code, 201)
        m = TicketMatch.objects.first()
        bad_link = self._create_link_payload()
        bad_link.pop("vendor")
        r = self.client.post(reverse("tickets:create_link", args=[m.match_id]), bad_link)
        self.assertEqual(r.status_code, 400)

    def test_tickets_root_url(self):
        r = self.client.get("/tickets/")
        self.assertEqual(r.status_code, 200)
