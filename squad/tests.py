# squad/tests.py
from __future__ import annotations
import json
import os
from uuid import uuid4
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from .models import Player
from . import views  # jika tidak dipakai, boleh dihapus


# ==== KONFIG URL NAME (SESUAIKAN JIKA BERBEDA) ====
INDEX_URL_NAME = "squad:index"
DETAIL_URL_NAME = "squad:player_detail"
CREATE_URL_NAME = "squad:player_create"
EDIT_URL_NAME   = "squad:player_edit"
DELETE_URL_NAME = "squad:player_delete"

SHOW_JSON_URL_NAME        = "squad:show_json"
SHOW_JSON_BY_ID_URL_NAME  = "squad:show_json_by_id"
SHOW_XML_URL_NAME         = "squad:show_xml"
SHOW_XML_BY_ID_URL_NAME   = "squad:show_xml_by_id"

AJAX_ADD_URL_NAME    = "squad:add_player_entry_ajax"
AJAX_DELETE_URL_NAME = "squad:delete_player_ajax"
# ==================================================


# ================== MODEL TESTS ===================
class PlayerModelTests(TestCase):
    def test_str_returns_name(self):
        p = Player.objects.create(name="Pratama Arhan")
        self.assertEqual(str(p), "Pratama Arhan")

    def test_fname_lname_multiword_and_single(self):
        p = Player.objects.create(name="Muhammad Ferdiansyah Ridho")
        self.assertEqual(p.fname, "Muhammad")
        self.assertEqual(p.lname, "Ferdiansyah Ridho")

        q = Player.objects.create(name="Ronaldo")
        self.assertEqual(q.fname, "Ronaldo")
        self.assertEqual(q.lname, "")

    def test_age_none_when_birth_date_missing(self):
        p = Player.objects.create(name="No DOB")
        self.assertIsNone(p.age)

    def test_age_calculation_edge_cases(self):
        today = date.today()
        born_passed = date(today.year - 20, 1, 1)
        p1 = Player.objects.create(name="A", birth_date=born_passed)
        exp1 = today.year - born_passed.year - ((today.month, today.day) < (born_passed.month, born_passed.day))
        self.assertEqual(p1.age, exp1)

        born_not_yet = date(today.year - 20, 12, 31)
        p2 = Player.objects.create(name="B", birth_date=born_not_yet)
        exp2 = today.year - born_not_yet.year - ((today.month, today.day) < (born_not_yet.month, born_not_yet.day))
        self.assertEqual(p2.age, exp2)

    def test_positions_list_and_display(self):
        p = Player.objects.create(name="W", position1="CM", position2="RW", position3="")
        self.assertEqual(p.positions_list, ["CM", "RW"])
        self.assertEqual(p.positions_display, "CM, RW")

        q = Player.objects.create(name="X")
        self.assertEqual(q.positions_list, [])
        self.assertEqual(q.positions_display, "")

    def test_role_tag_mapping(self):
        cases = [
            ("GK", "GOALKEEPER"),
            ("LB", "DEFENDER"),
            ("CB", "DEFENDER"),
            ("RWB", "DEFENDER"),
            ("CM", "MIDFIELDER"),
            ("CDM", "MIDFIELDER"),
            ("CAM", "MIDFIELDER"),
            ("ST", "ATTACKER"),
            ("RW", "ATTACKER"),
            ("", "MIDFIELDER"),
        ]
        for pos, expect in cases:
            with self.subTest(pos=pos):
                p = Player.objects.create(name=f"Y-{pos or 'blank'}", position1=pos)
                self.assertEqual(p.role_tag, expect)

    def test_defaults_and_created_at(self):
        p = Player.objects.create(name="Defaults Guy")
        self.assertEqual(p.caps, 0)
        self.assertEqual(p.goals, 0)
        self.assertEqual(p.assists, 0)
        self.assertIsNotNone(p.created_at)

    def test_photo_url_validation(self):
        p = Player(name="Bad URL", photo_url="not-a-url")
        with self.assertRaises(ValidationError) as ctx:
            p.full_clean()
        self.assertIn("photo_url", ctx.exception.message_dict)

    def test_positive_integer_validations(self):
        p = Player(name="Neg Caps", caps=-1)
        with self.assertRaises(ValidationError) as ctx1:
            p.full_clean()
        self.assertIn("caps", ctx1.exception.message_dict)

        q = Player(name="Neg Height", height_cm=-170)
        with self.assertRaises(ValidationError) as ctx2:
            q.full_clean()
        self.assertIn("height_cm", ctx2.exception.message_dict)


# ============== BASE SETUP UNTUK VIEW/API ==============
class BaseSquadTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rf = RequestFactory()

        User = get_user_model()
        # bersihkan tabel agar prediktabel
        Player.objects.all().delete()

        # user biasa
        self.user = User.objects.create_user(username="user", password="p", role="USER")

        # siapkan admin: pakai env jika ada (selaras dgn pola news/tests.py)
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

        # fixture pemain
        self.p1 = Player.objects.create(name="A_GK", position1="GK", club="X")
        self.p2 = Player.objects.create(name="B_LB", position1="LB", club="X")
        self.p3 = Player.objects.create(name="C_CM", position1="CM", club="Y")
        self.p4 = Player.objects.create(name="D_ST", position1="ST", club="Z")


# ============== HTML VIEWS (PUBLIC & ADMIN) ==============
class PublicAndHTMLViewsTests(BaseSquadTestCase):
    def test_index_ok(self):
        url = reverse(INDEX_URL_NAME)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_player_detail_ok(self):
        url = reverse(DETAIL_URL_NAME, kwargs={"pk": self.p1.id})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

