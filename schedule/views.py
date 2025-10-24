from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
)
from django.core import serializers
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required

from .models import NationalTeamSchedule
from .forms import NationalTeamScheduleForm


from collections import defaultdict
from datetime import datetime

def show_main(request):

    categories = [c[0] for c in NationalTeamSchedule._meta.get_field("category").choices]
    
    context = {
        "categories": categories,
    }
    return render(request, "schedule.html", context)


def show_match(request, match_id):
    match = get_object_or_404(NationalTeamSchedule, pk=match_id)

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
    # (Fungsi ini untuk halaman non-AJAX, biarkan saja)
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

def show_xml(request):
    xml_data = serializers.serialize("xml", NationalTeamSchedule.objects.all())
    return HttpResponse(xml_data, content_type="application/xml")

# Fungsi ini sekarang SANGAT PENTING untuk fetchMatchesFromServer
def show_json(request):
    data = [
        {
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
        }
        for m in NationalTeamSchedule.objects.all()
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
    }
    return JsonResponse(data)

@csrf_exempt
@require_POST
@login_required 
def add_match_ajax(request):
    # --- 1. Extract and sanitize data ---
    home_team = strip_tags(request.POST.get("home_team", "")).strip()
    away_team = strip_tags(request.POST.get("away_team", "")).strip()
    match_date = strip_tags(request.POST.get("match_date", "")).strip()
    location = strip_tags(request.POST.get("location", "")).strip()
    category = strip_tags(request.POST.get("category", "")).strip()

    if not (home_team and away_team and match_date and location and category):
        return HttpResponse(b"INVALID: Missing required fields", status=400)

    home_code = strip_tags(request.POST.get("home_code", "")).strip() or None
    away_code = strip_tags(request.POST.get("away_code", "")).strip() or None
    lineup = strip_tags(request.POST.get("lineup", "")) or None # Ambil lineup
    review = strip_tags(request.POST.get("review", "")) or None # Ambil review
    home_score = request.POST.get("home_score") or None # Ambil home_score
    away_score = request.POST.get("away_score") or None # Ambil away_score

    # Ambil semua field statistik
    shots_home=request.POST.get("shots_home") or None; shots_away=request.POST.get("shots_away") or None
    shots_on_target_home=request.POST.get("shots_on_target_home") or None; shots_on_target_away=request.POST.get("shots_on_target_away") or None
    possession_home=request.POST.get("possession_home") or None; possession_away=request.POST.get("possession_away") or None
    passes_home=request.POST.get("passes_home") or None; passes_away=request.POST.get("passes_away") or None
    pass_accuracy_home=request.POST.get("pass_accuracy_home") or None; pass_accuracy_away=request.POST.get("pass_accuracy_away") or None
    fouls_home=request.POST.get("fouls_home") or None; fouls_away=request.POST.get("fouls_away") or None
    yellow_cards_home=request.POST.get("yellow_cards_home") or None; yellow_cards_away=request.POST.get("yellow_cards_away") or None
    red_cards_home=request.POST.get("red_cards_home") or None; red_cards_away=request.POST.get("red_cards_away") or None
    offsides_home=request.POST.get("offsides_home") or None; offsides_away=request.POST.get("offsides_away") or None
    corners_home=request.POST.get("corners_home") or None; corners_away=request.POST.get("corners_away") or None

    try:
        # --- 2. Create the model instance directly (MENIRU NEWS) ---
        #    Pastikan SEMUA field dimasukkan di sini
        new_match = NationalTeamSchedule(
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            location=location,
            category=category,
            home_code=home_code,           # <-- Jangan lupa ini
            away_code=away_code,           # <-- Jangan lupa ini
            lineup=lineup,                 # <-- Jangan lupa ini
            review=review,                 # <-- Jangan lupa ini
            home_score=home_score,         # <-- Jangan lupa ini
            away_score=away_score,         # <-- Jangan lupa ini
            shots_home=shots_home,
            shots_away=shots_away,
            shots_on_target_home=shots_on_target_home,
            shots_on_target_away=shots_on_target_away,
            possession_home=possession_home,
            possession_away=possession_away,
            passes_home=passes_home,
            passes_away=passes_away,
            pass_accuracy_home=pass_accuracy_home,
            pass_accuracy_away=pass_accuracy_away,
            fouls_home=fouls_home,
            fouls_away=fouls_away,
            yellow_cards_home=yellow_cards_home,
            yellow_cards_away=yellow_cards_away,
            red_cards_home=red_cards_home,
            red_cards_away=red_cards_away,
            offsides_home=offsides_home,
            offsides_away=offsides_away,
            corners_home=corners_home,
            corners_away=corners_away
            # lineup_image_url tidak dipakai lagi
        )

        # --- 3. Save the instance (MENIRU NEWS) ---
        new_match.save()

        # --- 4. Return simple success response (MENIRU NEWS) ---
        return HttpResponse(b"CREATED", status=201)

    except Exception as e:
        # Basic error handling
        import traceback
        print(traceback.format_exc()) # Log error lengkap ke console server
        return HttpResponse(f"Error creating match: {e}".encode(), status=400)