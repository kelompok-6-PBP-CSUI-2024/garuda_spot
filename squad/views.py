# --- imports (perbaiki Http404 & tambah reverse) ---
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import date
from django.shortcuts import render, get_object_or_404
from .models import Player, POS_CHOICES
from django.contrib.auth.decorators import login_required

# kalau kamu punya ModelForm:
# from .forms import PlayerForm

ALLOWED_POS = {c[0] for c in POS_CHOICES if c[0]}

def index(request):
    players = Player.objects.all().order_by('created_at', 'name')
    return render(request, "squad/index.html", {"players": players})

@require_http_methods(["GET"])
def player_detail(request, pk):
    p = get_object_or_404(Player, pk=pk)
    return render(request, "squad/detail.html", {"p": p})

# ===================== RESTRICTED (admin only) =====================

@require_http_methods(["POST"])
@login_required
def player_delete(request, pk):
    # hanya admin
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
    # hanya admin
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")
    html = render_to_string(
        "squad/_player_form.html",
        {
            "POS_CHOICES": POS_CHOICES,
            "submit_url": reverse("squad:player_create"),
            "title": "Tambah Pemain",
            # "form": PlayerForm(),  # kalau kamu pakai Django Form
        },
        request=request
    )
    return JsonResponse({"html": html})

@require_http_methods(["POST"])
@login_required
def player_create(request):
    # hanya admin
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
    # hanya admin
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
                # "form": PlayerForm(instance=p),
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
