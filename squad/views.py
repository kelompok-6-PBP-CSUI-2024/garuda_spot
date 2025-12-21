from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt,ensure_csrf_cookie
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from datetime import date
import json
from django.template.loader import render_to_string
from django.urls import reverse


from .models import Player, POS_CHOICES

ALLOWED_POS = {c[0] for c in POS_CHOICES if c[0]}


def _parse_date(s: str | None):
    if not s:
        return None
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None


def _to_int(val, default=0, nonneg=False):
    try:
        v = int(val)
        if nonneg and v < 0:
            return default
        return v
    except (TypeError, ValueError):
        return default


def _pos(v: str | None):
    v = (v or "").strip().upper()
    return v if v in ALLOWED_POS else ""


def _player_to_dict(p: Player):
    return {
        "id": p.id,
        "name": p.name,
        "fname": p.fname,
        "lname": p.lname,
        "photo_url": p.photo_url,
        "birth_date": p.birth_date.isoformat() if p.birth_date else None,
        "age": p.age,
        "club": p.club,
        "height_cm": p.height_cm,
        "positions": p.positions_list,
        "role_tag": p.role_tag,
        "caps": p.caps,
        "goals": p.goals,
        "assists": p.assists,
    }


@require_http_methods(["GET"])
def api_players(request):
    players = Player.objects.all().order_by("name")
    return JsonResponse([_player_to_dict(p) for p in players], safe=False)


@require_http_methods(["GET"])
def api_player_detail(request, pk):
    p = get_object_or_404(Player, pk=pk)
    return JsonResponse(_player_to_dict(p))


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_player_create(request):
    if not getattr(request.user, "is_admin", False):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body.decode())
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    name = (data.get("name") or "").strip()
    if not name:
        return HttpResponseBadRequest("Name is required")

    p = Player.objects.create(
        name=name,
        photo_url=(data.get("photo_url") or "").strip(),
        club=(data.get("club") or "").strip(),
        birth_date=_parse_date(data.get("birth_date")),
        height_cm=_to_int(data.get("height_cm"), default=None, nonneg=True),
        position1=_pos(data.get("position1")),
        position2=_pos(data.get("position2")),
        position3=_pos(data.get("position3")),
        caps=_to_int(data.get("caps"), default=0, nonneg=True) or 0,
        goals=_to_int(data.get("goals"), default=0, nonneg=True) or 0,
        assists=_to_int(data.get("assists"), default=0, nonneg=True) or 0,
    )

    return JsonResponse(_player_to_dict(p), status=201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def api_player_update(request, pk):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    p = get_object_or_404(Player, pk=pk)

    if request.method == "GET":
        return JsonResponse(_player_to_dict(p))

    try:
        data = json.loads(request.body.decode())
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    name = data.get("name")
    if name is None or not str(name).strip():
        return HttpResponseBadRequest("Name is required")
    p.name = str(name).strip()

    if "photo_url" in data:
        p.photo_url = (data.get("photo_url") or "").strip()

    if "club" in data:
        p.club = (data.get("club") or "").strip()

    if "birth_date" in data:
        p.birth_date = _parse_date(data.get("birth_date"))

    if "height_cm" in data:
        p.height_cm = _to_int(data.get("height_cm"), default=None, nonneg=True)

    if "position1" in data:
        p.position1 = _pos(data.get("position1"))
    if "position2" in data:
        p.position2 = _pos(data.get("position2"))
    if "position3" in data:
        p.position3 = _pos(data.get("position3"))

    if "caps" in data:
        p.caps = _to_int(data.get("caps"), default=0, nonneg=True) or 0
    if "goals" in data:
        p.goals = _to_int(data.get("goals"), default=0, nonneg=True) or 0
    if "assists" in data:
        p.assists = _to_int(data.get("assists"), default=0, nonneg=True) or 0

    p.save()

    return JsonResponse(_player_to_dict(p))

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_player_delete(request, pk):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    p = get_object_or_404(Player, pk=pk)
    pid = p.id
    p.delete()
    return JsonResponse({"ok": True, "id": pid})
@require_http_methods(["GET"])
def api_players(request):
    players = Player.objects.all().order_by("id")
    data = [
        {
            "id": p.id,
            "name": p.name,
            "photo_url": p.photo_url or "",
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "club": p.club,
            "height_cm": p.height_cm,
            "position1": p.position1,
            "position2": p.position2,
            "position3": p.position3,
            "caps": p.caps,
            "goals": p.goals,
            "assists": p.assists,
            "role_tag": p.role_tag,
        }
        for p in players
    ]
    return JsonResponse(data, safe=False)

def index(request):
    players = Player.objects.all().order_by('created_at', 'name')
    return render(request, "squad/index.html", {"players": players})

@require_http_methods(["GET"])
def player_detail(request, pk):
    p = get_object_or_404(Player, pk=pk)
    return render(request, "squad/detail.html", {"p": p})


@require_http_methods(["POST"])
@login_required
def player_delete(request, pk):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")
    p = get_object_or_404(Player, pk=pk)
    pid = p.id
    p.delete()
    return JsonResponse({"ok": True, "id": pid})

@require_http_methods(["GET"])

@ensure_csrf_cookie
@login_required
def player_form(request):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")
    html = render_to_string(
        "squad/_player_form.html",
        {
            "POS_CHOICES": POS_CHOICES,
            "submit_url": reverse("squad:player_create"),
            "title": "Tambah Pemain",
        },
        request=request
    )
    return JsonResponse({"html": html})

@require_http_methods(["POST"])
@login_required
def player_create(request):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    name       = strip_tags(request.POST.get("name", "")).strip()
    photo_url  = strip_tags(request.POST.get("photo_url", "")).strip()
    club       = strip_tags(request.POST.get("club", "")).strip()

    def _parse_birth(s):
        if not s: return None
        try:
            y,m,d = (int(x) for x in s.split("-")); return date(y,m,d)
        except Exception:
            return None

    def _to_int(val, default=None, nonneg=False):
        try:
            v = int(val)
            if nonneg and v < 0: return default
            return v
        except (TypeError, ValueError):
            return default

    birth_date = _parse_birth(request.POST.get("birth_date"))
    height_cm  = _to_int(request.POST.get("height_cm"), default=None, nonneg=True)

    def _pos(x):
        v = strip_tags(request.POST.get(x, "")).strip().upper()
        return v if v in ALLOWED_POS else ""

    position1  = _pos("position1")
    position2  = _pos("position2")
    position3  = _pos("position3")

    caps       = _to_int(request.POST.get("caps"), default=0, nonneg=True) or 0
    goals      = _to_int(request.POST.get("goals"), default=0, nonneg=True) or 0
    assists    = _to_int(request.POST.get("assists"), default=0, nonneg=True) or 0

    if not name:
        return HttpResponseBadRequest("Nama pemain wajib diisi.")

    p = Player.objects.create(
        name=name,
        photo_url=photo_url or "",
        club=club or "",
        birth_date=birth_date,
        height_cm=height_cm,
        position1=position1,
        position2=position2,
        position3=position3,
        caps=caps,
        goals=goals,
        assists=assists,
    )

    card_html = render_to_string("squad/_player_card.html", {"p": p}, request=request)
    return JsonResponse({"id": p.id, "role_tag": p.role_tag, "html": card_html}, status=201)

@require_http_methods(["GET", "POST"])
@login_required
def player_edit(request, pk):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    try:
        p = Player.objects.get(pk=pk)
    except Player.DoesNotExist:
        raise Http404("Player not found")

    if request.method == "GET":
        html = render_to_string(
            "squad/_player_form.html",
            {
                "p": p,
                "POS_CHOICES": POS_CHOICES,
                "submit_url": reverse("squad:player_edit", args=[p.id]),
                "title": f"Edit {p.name}",
            },
            request=request
        )
        return JsonResponse({"html": html})

    old_role = p.role_tag

    def _parse_birth(s):
        if not s: return None
        try:
            y,m,d = (int(x) for x in s.split("-")); return date(y,m,d)
        except Exception:
            return None

    def _to_int(val, default=None, nonneg=False):
        try:
            v = int(val)
            if nonneg and v < 0: return default
            return v
        except (TypeError, ValueError):
            return default

    p.name       = strip_tags(request.POST.get("name", "")).strip() or p.name
    p.photo_url  = strip_tags(request.POST.get("photo_url", "")).strip()
    p.club       = strip_tags(request.POST.get("club", "")).strip()
    p.birth_date = _parse_birth(request.POST.get("birth_date"))
    p.height_cm  = _to_int(request.POST.get("height_cm"), default=None, nonneg=True)

    def _pos(x):
        v = strip_tags(request.POST.get(x, "")).strip().upper()
        return v if (not v) or (v in ALLOWED_POS) else ""

    p.position1 = _pos("position1")
    p.position2 = _pos("position2")
    p.position3 = _pos("position3")

    p.caps    = _to_int(request.POST.get("caps"), default=0, nonneg=True) or 0
    p.goals   = _to_int(request.POST.get("goals"), default=0, nonneg=True) or 0
    p.assists = _to_int(request.POST.get("assists"), default=0, nonneg=True) or 0

    if not p.name:
        return HttpResponseBadRequest("Nama pemain wajib diisi.")

    p.save()

    moved = (old_role != p.role_tag)
    card_html = render_to_string("squad/_player_card.html", {"p": p}, request=request)
    return JsonResponse({"id": p.id, "role_tag": p.role_tag, "html": card_html, "moved": moved})

@require_http_methods(["GET"])
def api_players(request):
    players = Player.objects.all().order_by("name")

    data = []
    for p in players:
        data.append({
            "id": p.id,
            "name": p.name,
            "fname": p.fname,
            "lname": p.lname,
            "photo_url": p.photo_url,
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "age": p.age,
            "club": p.club,
            "height_cm": p.height_cm,

            "positions": p.positions_list,
            "positions_display": p.positions_display,
            "role_tag": p.role_tag,

            "caps": p.caps,
            "goals": p.goals,
            "assists": p.assists,
        })

    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def api_player_detail(request, pk):
    p = get_object_or_404(Player, pk=pk)

    data = {
        "id": p.id,
        "name": p.name,
        "photo_url": p.photo_url,
        "age": p.age,
        "club": p.club,
        "height_cm": p.height_cm,
        "positions": p.positions_list,
        "role_tag": p.role_tag,
        "caps": p.caps,
        "goals": p.goals,
        "assists": p.assists,
    }
    return JsonResponse(data)
