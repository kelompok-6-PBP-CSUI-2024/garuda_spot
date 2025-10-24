# views.py (FINAL DAN KOREKSI)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
)
from django.core import serializers
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required

from .models import NationalTeamSchedule
from .forms import NationalTeamScheduleForm
import uuid # Diperlukan karena Anda menggunakan UUID

# --- Helper Function (Dipertahankan) ---
# Tidak ada perubahan pada helper Anda, kecuali penamaan agar tidak konflik.
# Asumsikan helper to_int ada di bagian atas views.py
# def to_int(val, default=0): ...

# --- FUNGSI UTAMA NON-AJAX ---

def show_main(request):
    categories = [c[0] for c in NationalTeamSchedule._meta.get_field("category").choices]
    context = {
        "categories": categories,
    }
    return render(request, "schedule.html", context)


def show_match(request, match_id):
    match = get_object_or_404(NationalTeamSchedule, pk=match_id)
    # ... (Stats logic) ...
    stats = [
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
    return render(request, "match_detail.html", {"match": match, "stats": stats})

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

# --- FUNGSI DATA FEED (JSON/XML) ---
# ... (show_xml, show_json, show_xml_by_id, show_json_by_id - TIDAK DIUBAH) ...

def show_xml(request):
    xml_data = serializers.serialize("xml", NationalTeamSchedule.objects.all())
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    # Ditingkatkan untuk menyertakan semua data yang dibutuhkan frontend Edit modal
    data = [
        {
            "id": str(m.id), "home_team": m.home_team, "away_team": m.away_team,
            "match_date": m.match_date, "location": m.location, "category": m.category,
            "home_score": m.home_score, "away_score": m.away_score,
            "home_code": m.home_code, "away_code": m.away_code, "category_image_url": m.category_image_url,
            "lineup": m.lineup, "review": m.review,
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
        for m in NationalTeamSchedule.objects.all().order_by('-match_date')
    ]
    return JsonResponse(data, safe=False)

def show_xml_by_id(request, match_id):
    qs = NationalTeamSchedule.objects.filter(pk=match_id)
    xml_data = serializers.serialize("xml", qs)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json_by_id(request, match_id):
    try:
        m = NationalTeamSchedule.objects.get(pk=match_id)
    except NationalTeamSchedule.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)

    data = {
        "id": str(m.id), "home_team": m.home_team, "away_team": m.away_team,
        "match_date": m.match_date, "location": m.location, "category": m.category,
        "home_score": m.home_score, "away_score": m.away_score,
        "home_code": m.home_code, "away_code": m.away_code, "category_image_url": m.category_image_url,
        "lineup": m.lineup, "review": m.review,
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
    return JsonResponse(data)

# --- FUNGSI CREATE AJAX (VERSI ASLI ANDA) ---
@csrf_exempt
@require_POST
@login_required 
def create_match_ajax(request):
    data = request.POST

    home_team = strip_tags(data.get("home_team", "")).strip()
    away_team = strip_tags(data.get("away_team", "")).strip()
    match_date = strip_tags(data.get("match_date", "")).strip()
    location = strip_tags(data.get("location", "")).strip()
    category = strip_tags(data.get("category", "")).strip()

    if not (home_team and away_team and match_date and location and category):
        return HttpResponse(b"INVALID: Missing required fields", status=400)

    fields = {
        "home_code": strip_tags(data.get("home_code", "")).strip() or None,
        "away_code": strip_tags(data.get("away_code", "")).strip() or None,
        "lineup": data.get("lineup") or None,
        "review": data.get("review") or None,
        "home_score": data.get("home_score") or None,
        "away_score": data.get("away_score") or None,
        "shots_home": data.get("shots_home") or None, "shots_away": data.get("shots_away") or None,
        "shots_on_target_home": data.get("shots_on_target_home") or None, "shots_on_target_away": data.get("shots_on_target_away") or None,
        "possession_home": data.get("possession_home") or None, "possession_away": data.get("possession_away") or None,
        "passes_home": data.get("passes_home") or None, "passes_away": data.get("passes_away") or None,
        "pass_accuracy_home": data.get("pass_accuracy_home") or None, "pass_accuracy_away": data.get("pass_accuracy_away") or None,
        "fouls_home": data.get("fouls_home") or None, "fouls_away": data.get("fouls_away") or None,
        "yellow_cards_home": data.get("yellow_cards_home") or None, "yellow_cards_away": data.get("yellow_cards_away") or None,
        "red_cards_home": data.get("red_cards_home") or None, "red_cards_away": data.get("red_cards_away") or None,
        "offsides_home": data.get("offsides_home") or None, "offsides_away": data.get("offsides_away") or None,
        "corners_home": data.get("corners_home") or None, "corners_away": data.get("corners_away") or None,
    }
    
    try:
        new_match = NationalTeamSchedule(
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            location=location,
            category=category,
            **fields
        )
        new_match.save()
        return HttpResponse(b"CREATED", status=201)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return HttpResponse(f"Error creating match: {e}".encode(), status=400)


# --- FUNGSI UPDATE AJAX (Bergaya Merch, menggunakan form untuk validasi) ---
@csrf_exempt
@require_POST
@login_required 
def update_match_ajax(request, match_id):
    if not request.user.is_admin:
        return HttpResponseForbidden(b"Unauthorized")

    match = get_object_or_404(NationalTeamSchedule, pk=match_id)
    
    # Menggunakan form untuk memproses dan memvalidasi
    form = NationalTeamScheduleForm(request.POST, instance=match)

    if form.is_valid():
        updated_match = form.save()
        
        # Kembalikan JSON dengan data yang diupdate (penting untuk frontend)
        data_response = {
            "id": str(updated_match.id), 
            "home_team": updated_match.home_team, 
            "away_team": updated_match.away_team, 
            "match_date": updated_match.match_date, 
            "category": updated_match.category, 
            "location": updated_match.location,
            "home_score": updated_match.home_score,
            "away_score": updated_match.away_score,
            "home_code": updated_match.home_code,
            "away_code": updated_match.away_code,
            "lineup": updated_match.lineup,
            "review": updated_match.review,
            # Statistik harus dikirim balik jika form perlu diperbarui di modal
            "shots_home": updated_match.shots_home, "shots_away": updated_match.shots_away,
            # ... (semua field statistik) ...
        }
        return JsonResponse(data_response, status=200) 
    else:
        # Kembalikan error form JSON (seperti Merch update)
        errors = dict(form.errors.items())
        return JsonResponse({'detail': 'Validation failed', 'errors': errors}, status=400)


# --- FUNGSI DELETE AJAX (Bergaya Merch) ---
@csrf_exempt
@require_POST
@login_required 
def delete_match_ajax(request, match_id):
    if not request.user.is_admin:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    try:
        match = get_object_or_404(NationalTeamSchedule, pk=match_id)
    except Exception:
        return JsonResponse({"detail": "Not found"}, status=404)

    match.delete()
    # Kembalikan status 200 OK dengan ID yang dihapus (seperti Merch delete)
    return JsonResponse({"deleted": match_id}, status=200)