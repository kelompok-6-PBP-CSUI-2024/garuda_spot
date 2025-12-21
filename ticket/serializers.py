from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .models import TicketLink, TicketMatch


def serialize_link(link: TicketLink) -> Dict[str, Any]:
    return {
        "id": link.id,
        "link_id": str(link.link_id),
        "vendor": link.vendor,
        "vendor_link": link.vendor_link,
        "price": link.price,
        "img_vendor": link.img_vendor,
    }


def serialize_match(match: TicketMatch, include_links: bool = True) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "id": match.id,
        "match_id": str(match.match_id),
        "team1": match.team1,
        "team2": match.team2,
        "img_team1": match.img_team1,
        "img_team2": match.img_team2,
        "img_cup": match.img_cup,
        "place": match.place,
        "date": match.date,
    }
    if include_links:
        data["links"] = [serialize_link(link) for link in match.links.all().order_by("id")]
    return data


def _coerce_mapping(payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "dict"):
        return payload.dict()
    try:
        return {
            key: (vals[0] if isinstance(vals, list) and len(vals) == 1 else vals)
            for key, vals in payload.items()
        }
    except Exception:
        return {}


def parse_match_payload(payload: Any) -> Dict[str, Any]:
    allowed_fields = {
        "team1",
        "team2",
        "img_team1",
        "img_team2",
        "img_cup",
        "place",
        "date",
    }
    data = _coerce_mapping(payload)
    return {k: v for k, v in data.items() if k in allowed_fields}


def parse_link_payload(payload: Any) -> Dict[str, Any]:
    allowed_fields = {
        "vendor",
        "vendor_link",
        "price",
        "img_vendor",
    }
    data = _coerce_mapping(payload)
    return {k: v for k, v in data.items() if k in allowed_fields}
