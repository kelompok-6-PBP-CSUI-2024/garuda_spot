"""
Simple API smoke test for ticket endpoints.

Usage examples:
  python ticket/api_smoke_test.py --base http://localhost:8000
  python ticket/api_smoke_test.py --base https://hasanul-muttaqin-garudaspot.pbp.cs.ui.ac.id --uuid 123e4567-e89b-12d3-a456-426614174000
  python ticket/api_smoke_test.py --base https://... --sessionid <cookie> --csrftoken <token> --create

Notes:
- Create/edit endpoints require an admin session. Supply session cookies from a logged-in admin browser (`sessionid` and, if CSRF is enforced, `csrftoken`).
- By default, the script only performs GET checks. Pass `--create` to attempt a create+delete round-trip.
"""

from __future__ import annotations

import argparse
import sys
import uuid as uuidlib
from datetime import date

import requests


def build_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def check_get(session: requests.Session, url: str, label: str) -> bool:
    try:
        res = session.get(url, timeout=10)
        ok = res.status_code == 200
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {label}: {exc}")
        return False
    else:
        print(f"[{'OK' if ok else 'FAIL'}] {label}: {res.status_code}")
        if not ok:
            print(res.text[:500])
        return ok


def do_create_round_trip(session: requests.Session, base: str, use_json: bool = False) -> bool:
    """Attempt to create a match, add a link, then delete both (best-effort)."""
    match_payload = {
        "team1": "SmokeTest A",
        "team2": "SmokeTest B",
        "img_team1": "https://picsum.photos/seed/smokea/64",
        "img_team2": "https://picsum.photos/seed/smokeb/64",
        "img_cup": "",
        "place": "Smoke Arena",
        "date": date.today().isoformat(),
    }
    create_url = build_url(base, "/tickets/create/")
    try:
        res = session.post(
            create_url,
            json=match_payload if use_json else None,
            data=None if use_json else match_payload,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] create match: {exc}")
        return False
    if res.status_code not in (200, 201):
        print(f"[FAIL] create match: {res.status_code} {res.text[:400]}")
        return False
    print("[OK] create match")

    # Fetch all to find the created one (by team name)
    list_url = build_url(base, "/tickets/json/")
    res_list = session.get(list_url, timeout=10)
    res_list.raise_for_status()
    matches = res_list.json() if res_list.headers.get("content-type", "").startswith("application/json") else []
    created = next((m for m in matches if m.get("team1") == "SmokeTest A" and m.get("team2") == "SmokeTest B"), None)
    if not created:
        print("[FAIL] created match not found in list")
        return False

    match_uuid = created.get("match_id")
    if not match_uuid:
        print("[FAIL] created match missing match_id")
        return False

    link_payload = {
        "vendor": "SmokeVendor",
        "vendor_link": "https://example.com/smoke",
        "price": 123456,
        "img_vendor": "https://picsum.photos/seed/smokelink/64",
    }
    create_link_url = build_url(base, f"/tickets/link/create/{match_uuid}/")
    res_link = session.post(
        create_link_url,
        json=link_payload if use_json else None,
        data=None if use_json else link_payload,
        timeout=10,
    )
    if res_link.status_code not in (200, 201):
        print(f"[FAIL] create link: {res_link.status_code} {res_link.text[:400]}")
        return False
    print("[OK] create link")

    # Best-effort cleanup
    session.post(build_url(base, f"/tickets/delete/{match_uuid}/"), timeout=10)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test ticket endpoints.")
    parser.add_argument("--base", default="http://localhost:8000", help="Base URL (e.g. https://hasanul-muttaqin-garudaspot.pbp.cs.ui.ac.id)")
    parser.add_argument("--uuid", help="Match UUID to check detail endpoints (optional)")
    parser.add_argument("--sessionid", help="sessionid cookie for admin session (optional, required for create)")
    parser.add_argument("--csrftoken", help="csrftoken cookie if needed (optional)")
    parser.add_argument("--create", action="store_true", help="Attempt create/link/delete round-trip (admin only)")
    parser.add_argument("--as-json", action="store_true", help="Send create/link as JSON instead of form-data")
    args = parser.parse_args(argv)

    base = args.base
    session = requests.Session()
    if args.sessionid:
        session.cookies.set("sessionid", args.sessionid)
    if args.csrftoken:
        session.cookies.set("csrftoken", args.csrftoken)

    success = True
    success &= check_get(session, build_url(base, "/tickets/json/"), "list json")
    success &= check_get(session, build_url(base, "/tickets/xml/"), "list xml")

    # Check detail if uuid provided
    if args.uuid:
        try:
            uuidlib.UUID(str(args.uuid))
            uuid_str = str(args.uuid)
        except Exception:
            print("[FAIL] invalid uuid format")
            success = False
        else:
            success &= check_get(session, build_url(base, f"/tickets/json/{uuid_str}/"), "detail json (uuid)")
            success &= check_get(session, build_url(base, f"/tickets/xml/{uuid_str}/"), "detail xml (uuid)")

    if args.create:
        success &= do_create_round_trip(session, base, use_json=args.as_json)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
