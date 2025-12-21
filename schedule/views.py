from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
)
from django.core import serializers
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import NationalTeamSchedule
from .forms import NationalTeamScheduleForm
import json
import uuid 

# --- Helper untuk mapping data ke Dictionary ---
def match_to_dict(m):
    return {
        "id": str(m.id), 
        "home_team": m.home_team, 
        "away_team": m.away_team,
        "match_date": m.match_date, 
        "location": m.location, 
        "category": m.category,
        "home_score": m.home_score, 
        "away_score": m.away_score,
        "home_code": m.home_code, 
        "away_code": m.away_code, 
        "category_image_url": m.category_image_url,
        "lineup": m.lineup, 
        "review": m.review,
        # Stats
        "shots_home": m.shots_home, "shots_away": m.shots_away,
        "shots_on_target_home": m.shots_on_target_home, "shots_on_target_away": m.shots_on_target_away,
        "possession_home": m.possession_home, "possession_away": m.possession_away,
        "passes_home": m.passes_home, "passes_away": m.passes_away,
        "pass_accuracy_home": m.pass_accuracy_home, "pass_accuracy_away": m.pass_accuracy_away,
        "fouls_home": m.fouls_home, "fouls_away": m.fouls_away,
        "yellow_cards_home": m.yellow_cards_home, "yellow_cards_away": m.yellow_cards_away,
        "red_cards_home": m.red_cards_home, "red_cards_away": m.red_cards_away,
        "offsides_home": m.offsides_home, "offsides_away": m.offsides_away,
        "corners_home": m.corners_home, "corners_away": m.corners_away
    }

# --- Main Views ---

def show_main(request):
    categories = [c[0] for c in NationalTeamSchedule._meta.get_field("category").choices]
    return render(request, "schedule.html", {"categories": categories})

def show_match(request, match_id):
    match = get_object_or_404(NationalTeamSchedule, pk=match_id)
    
    # Logic statistik untuk template
    raw_stats = [
        ("Shots", match.shots_home, match.shots_away),
        ("Shots on Target", match.shots_on_target_home, match.shots_on_target_away),
        ("Possession (%)", match.possession_home, match.possession_away),
        ("Passes", match.passes_home, match.passes_away),
        ("Pass Accuracy (%)", match.pass_accuracy_home, match.pass_accuracy_away),
        ("Fouls", match.fouls_home, match.fouls_away),
        ("Yellow Cards", match.yellow_cards_home, match.yellow_cards_away),
        ("Red Cards", match.red_cards_home, match.red_cards_away),
        ("Offsides", match.offsides_home, match.offsides_away),
        ("Corners", match.corners_home, match.corners_away),
    ]

    stats_for_template = []
    for stat_name, home_val, away_val in raw_stats:
        home = int(home_val) if home_val is not None else 0
        away = int(away_val) if away_val is not None else 0
        total = home + away
        
        home_percent = 50
        away_percent = 50
        
        if total > 0:
            home_percent = round((home / total) * 100)
            away_percent = 100 - home_percent

        stats_for_template.append({
            "name": stat_name,
            "home_val": home,
            "away_val": away,
            "home_percent": home_percent,
            "away_percent": away_percent
        })

    return render(request, "match_detail.html", {"match": match, "stats": stats_for_template})

@login_required
def create_match(request):
    form = NationalTeamScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('schedule:show_main') 
    return render(request, "create_match.html", {"form": form})

@login_required
def edit_match(request, id):
    match = get_object_or_404(NationalTeamSchedule, pk=id)
    form = NationalTeamScheduleForm(request.POST or None, instance=match)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('schedule:show_match', match_id=match.id)
    return render(request, "edit_match.html", {"form": form, "match": match})

@login_required
def delete_match(request, id):
    match = get_object_or_404(NationalTeamSchedule, pk=id)
    match.delete()
    return HttpResponseRedirect(reverse('schedule:show_main')) 

# --- Data Feeds & API ---

def show_xml(request):
    xml_data = serializers.serialize("xml", NationalTeamSchedule.objects.all())
    return HttpResponse(xml_data, content_type="application/xml")

def show_xml_by_id(request, id):
    qs = NationalTeamSchedule.objects.filter(pk=id)
    xml_data = serializers.serialize("xml", qs)
    return HttpResponse(xml_data, content_type="application/xml")

@require_GET
def show_json(request):
    # Sorting logic similar to news
    sort_order = (request.GET.get("sort") or "desc").lower()
    
    # Asumsi match_date adalah field Date/DateTime yang valid di model
    if sort_order == "asc":
        qs = NationalTeamSchedule.objects.all().order_by('match_date')
    else:
        qs = NationalTeamSchedule.objects.all().order_by('-match_date')

    # Pagination logic
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    
    try:
        page_size = int(request.GET.get("page_size", 20))
    except ValueError:
        page_size = 20
    page_size = max(1, min(page_size, 100))

    paginator = Paginator(qs, page_size)
    
    try:
        matches_page = paginator.page(page)
    except Exception:
        # Jika page tidak valid (misal page 999), return empty list atau page terakhir
        matches_page = []

    data_items = [match_to_dict(m) for m in matches_page]

    return JsonResponse({
        "items": data_items,
        "page": page,
        "page_size": page_size,
        "has_next": matches_page.has_next() if hasattr(matches_page, 'has_next') else False,
        "total": paginator.count,
    })

def show_json_by_id(request, id):
    try:
        m = NationalTeamSchedule.objects.get(pk=id)
    except NationalTeamSchedule.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)
    return JsonResponse(match_to_dict(m))

# --- AJAX Web Views (Login Required) ---

@csrf_exempt
@require_POST
@login_required 
def create_match_ajax(request):
    # Logika sama seperti sebelumnya
    data = request.POST
    home_team = strip_tags(data.get("home_team", "")).strip()
    away_team = strip_tags(data.get("away_team", "")).strip()
    match_date = strip_tags(data.get("match_date", "")).strip()
    location = strip_tags(data.get("location", "")).strip()
    category = strip_tags(data.get("category", "")).strip()

    if not (home_team and away_team and match_date and location and category):
        return HttpResponse(b"INVALID: Missing required fields", status=400)

    # Helper untuk mengambil field opsional agar tidak berulang
    def get_val(key): return data.get(key) or None

    try:
        new_match = NationalTeamSchedule.objects.create(
            home_team=home_team, away_team=away_team, match_date=match_date,
            location=location, category=category,
            home_code=strip_tags(data.get("home_code", "")).strip() or None,
            away_code=strip_tags(data.get("away_code", "")).strip() or None,
            lineup=get_val("lineup"), review=get_val("review"),
            home_score=get_val("home_score"), away_score=get_val("away_score"),
            shots_home=get_val("shots_home"), shots_away=get_val("shots_away"),
            shots_on_target_home=get_val("shots_on_target_home"), shots_on_target_away=get_val("shots_on_target_away"),
            possession_home=get_val("possession_home"), possession_away=get_val("possession_away"),
            passes_home=get_val("passes_home"), passes_away=get_val("passes_away"),
            pass_accuracy_home=get_val("pass_accuracy_home"), pass_accuracy_away=get_val("pass_accuracy_away"),
            fouls_home=get_val("fouls_home"), fouls_away=get_val("fouls_away"),
            yellow_cards_home=get_val("yellow_cards_home"), yellow_cards_away=get_val("yellow_cards_away"),
            red_cards_home=get_val("red_cards_home"), red_cards_away=get_val("red_cards_away"),
            offsides_home=get_val("offsides_home"), offsides_away=get_val("offsides_away"),
            corners_home=get_val("corners_home"), corners_away=get_val("corners_away"),
        )
        return HttpResponse(b"CREATED", status=201)
    except Exception as e:
        return HttpResponse(f"Error creating match: {e}".encode(), status=400)

@csrf_exempt
@require_POST
@login_required 
def update_match_ajax(request, match_id):
    if not request.user.is_admin: # Asumsi properti is_admin ada
        return HttpResponseForbidden(b"Unauthorized")

    match = get_object_or_404(NationalTeamSchedule, pk=match_id)
    form = NationalTeamScheduleForm(request.POST, instance=match)

    if form.is_valid():
        updated_match = form.save()
        return JsonResponse(match_to_dict(updated_match), status=200) 
    else:
        errors = dict(form.errors.items())
        return JsonResponse({'detail': 'Validation failed', 'errors': errors}, status=400)

@csrf_exempt
@require_POST
@login_required 
def delete_match_ajax(request, match_id):
    if not getattr(request.user, "is_admin", False):
        return JsonResponse({"detail": "Forbidden"}, status=403)
    try:
        match = get_object_or_404(NationalTeamSchedule, pk=match_id)
        match.delete()
        return JsonResponse({"deleted": str(match_id)}, status=200)
    except Exception:
        return JsonResponse({"detail": "Not found"}, status=404)

# --- Mobile / API Views (CSRF Exempt) ---

@csrf_exempt
@require_POST
def add_match_mobile(request):
    """
    CSRF-exempt create endpoint untuk mobile/Flutter.
    Menerima Form-Data atau JSON Body.
    """
    if not (request.user.is_authenticated and getattr(request.user, "is_admin", False)):
        return HttpResponseForbidden("Admins only")

    # Handle JSON Body vs Form Data
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            data = {}
    else:
        data = request.POST

    # Validasi field utama
    home_team = strip_tags(data.get("home_team", "")).strip()
    away_team = strip_tags(data.get("away_team", "")).strip()
    match_date = strip_tags(data.get("match_date", "")).strip()
    location = strip_tags(data.get("location", "")).strip()
    category = strip_tags(data.get("category", "")).strip()

    if not (home_team and away_team and match_date and location and category):
        return JsonResponse({"error": "Missing required fields (home/away team, date, location, category)"}, status=400)

    # Helper untuk data
    def get_val(key): return data.get(key) or None

    try:
        new_match = NationalTeamSchedule.objects.create(
            home_team=home_team, away_team=away_team, match_date=match_date,
            location=location, category=category,
            home_code=strip_tags(data.get("home_code", "")).strip() or None,
            away_code=strip_tags(data.get("away_code", "")).strip() or None,
            lineup=get_val("lineup"), review=get_val("review"),
            home_score=get_val("home_score"), away_score=get_val("away_score"),
            shots_home=get_val("shots_home"), shots_away=get_val("shots_away"),
            shots_on_target_home=get_val("shots_on_target_home"), shots_on_target_away=get_val("shots_on_target_away"),
            possession_home=get_val("possession_home"), possession_away=get_val("possession_away"),
            passes_home=get_val("passes_home"), passes_away=get_val("passes_away"),
            pass_accuracy_home=get_val("pass_accuracy_home"), pass_accuracy_away=get_val("pass_accuracy_away"),
            fouls_home=get_val("fouls_home"), fouls_away=get_val("fouls_away"),
            yellow_cards_home=get_val("yellow_cards_home"), yellow_cards_away=get_val("yellow_cards_away"),
            red_cards_home=get_val("red_cards_home"), red_cards_away=get_val("red_cards_away"),
            offsides_home=get_val("offsides_home"), offsides_away=get_val("offsides_away"),
            corners_home=get_val("corners_home"), corners_away=get_val("corners_away"),
        )
        return JsonResponse(match_to_dict(new_match), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_POST
def delete_match_mobile(request, id):
    if not (request.user.is_authenticated and getattr(request.user, "is_admin", False)):
        return HttpResponseForbidden("Admins only")
    
    match = get_object_or_404(NationalTeamSchedule, pk=id)
    match.delete()
    return JsonResponse({"deleted": str(id)})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_match(request):
    """
    Endpoint gabungan untuk Mobile:
    GET: Return JSON list (via show_json)
    POST: Create new match (via add_match_mobile logic)
    """
    if request.method == "GET":
        return show_json(request)
    
    # Logic POST (Create)
    if not (request.user.is_authenticated and getattr(request.user, "is_admin", False)):
        return HttpResponseForbidden("Admins only")
    
    # Gunakan logic yang sama dengan add_match_mobile
    return add_match_mobile(request)

@csrf_exempt
@require_POST
def edit_match_mobile(request, id):
    """
    Endpoint edit match khusus mobile/API (JSON & Form Data).
    """
    # 1. Cek Admin
    if not (request.user.is_authenticated and getattr(request.user, "is_admin", False)):
        return HttpResponseForbidden("Admins only")

    # 2. Ambil Match Object
    match = get_object_or_404(NationalTeamSchedule, pk=id)

    # 3. Handle JSON Body vs Form Data
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            data = {}
    else:
        data = request.POST

    # 4. Update Field String (Hanya jika key ada di data)
    if "home_team" in data:
        match.home_team = strip_tags(data.get("home_team", match.home_team)).strip()
    if "away_team" in data:
        match.away_team = strip_tags(data.get("away_team", match.away_team)).strip()
    if "match_date" in data:
        match.match_date = strip_tags(data.get("match_date", match.match_date)).strip()
    if "location" in data:
        match.location = strip_tags(data.get("location", match.location)).strip()
    if "category" in data:
        match.category = strip_tags(data.get("category", match.category)).strip()
    
    # Update Codes (Optional fields)
    if "home_code" in data:
        match.home_code = strip_tags(data.get("home_code", "")).strip() or None
    if "away_code" in data:
        match.away_code = strip_tags(data.get("away_code", "")).strip() or None
    
    # Update Text Fields
    if "lineup" in data:
        match.lineup = data.get("lineup")
    if "review" in data:
        match.review = data.get("review")

    # 5. Helper untuk Update Stats (Angka/Integer)
    # Fungsi ini mengecek apakah key ada di data. Jika ada, update. Jika tidak, biarkan lama.
    def update_stat(key, current_value):
        if key in data:
            val = data.get(key)
            # Jika dikirim null/None atau string kosong, set jadi None (atau 0 tergantung model)
            if val == "" or val is None:
                return None 
            try:
                return int(val)
            except ValueError:
                return current_value
        return current_value

    match.home_score = update_stat("home_score", match.home_score)
    match.away_score = update_stat("away_score", match.away_score)
    
    match.shots_home = update_stat("shots_home", match.shots_home)
    match.shots_away = update_stat("shots_away", match.shots_away)
    
    match.shots_on_target_home = update_stat("shots_on_target_home", match.shots_on_target_home)
    match.shots_on_target_away = update_stat("shots_on_target_away", match.shots_on_target_away)
    
    match.possession_home = update_stat("possession_home", match.possession_home)
    match.possession_away = update_stat("possession_away", match.possession_away)
    
    match.passes_home = update_stat("passes_home", match.passes_home)
    match.passes_away = update_stat("passes_away", match.passes_away)
    
    match.pass_accuracy_home = update_stat("pass_accuracy_home", match.pass_accuracy_home)
    match.pass_accuracy_away = update_stat("pass_accuracy_away", match.pass_accuracy_away)
    
    match.fouls_home = update_stat("fouls_home", match.fouls_home)
    match.fouls_away = update_stat("fouls_away", match.fouls_away)
    
    match.yellow_cards_home = update_stat("yellow_cards_home", match.yellow_cards_home)
    match.yellow_cards_away = update_stat("yellow_cards_away", match.yellow_cards_away)
    
    match.red_cards_home = update_stat("red_cards_home", match.red_cards_home)
    match.red_cards_away = update_stat("red_cards_away", match.red_cards_away)
    
    match.offsides_home = update_stat("offsides_home", match.offsides_home)
    match.offsides_away = update_stat("offsides_away", match.offsides_away)
    
    match.corners_home = update_stat("corners_home", match.corners_home)
    match.corners_away = update_stat("corners_away", match.corners_away)

    # 6. Simpan
    try:
        match.save()
        return JsonResponse(match_to_dict(match), status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)