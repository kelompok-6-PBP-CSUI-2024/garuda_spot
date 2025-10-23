from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core import serializers
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

from .models import TicketMatch, TicketLink


def main_view(request):
    return render(request, "tickets_main.html")


# ----- Forms (HTML fragments for modals) -----
def form_match(request, match_uuid=None):
    instance = None
    if match_uuid:
        instance = get_object_or_404(TicketMatch, uuid=match_uuid)
    return render(request, "gen_tick_match.html", {"match": instance})


def form_link(request, match_uuid):
    match = get_object_or_404(TicketMatch, uuid=match_uuid)
    return render(request, "gen_tick_link.html", {"match": match})


# ----- AJAX endpoints for create/update -----
@csrf_exempt
@require_POST
def create_ticket_ajax(request):
    team1 = strip_tags(request.POST.get("team1", "")).strip()
    team2 = strip_tags(request.POST.get("team2", "")).strip()
    img_team1 = request.POST.get("img_team1", "").strip()
    img_team2 = request.POST.get("img_team2", "").strip()
    img_arena = request.POST.get("img_arena", "").strip() or None
    date = request.POST.get("date", "").strip()

    if not (team1 and team2 and img_team1 and img_team2 and date):
        return HttpResponse(b"INVALID", status=400)

    TicketMatch.objects.create(
        team1=team1,
        team2=team2,
        img_team1=img_team1,
        img_team2=img_team2,
        img_arena=img_arena,
        date=date,
    )
    return HttpResponse(b"CREATED", status=201)


@csrf_exempt
@require_POST
def edit_ticket_ajax(request, id):
    match = get_object_or_404(TicketMatch, uuid=id)
    team1 = strip_tags(request.POST.get("team1", match.team1)).strip()
    team2 = strip_tags(request.POST.get("team2", match.team2)).strip()
    img_team1 = request.POST.get("img_team1", match.img_team1).strip()
    img_team2 = request.POST.get("img_team2", match.img_team2).strip()
    img_arena = request.POST.get("img_arena", match.img_arena or "").strip() or None
    date = request.POST.get("date", str(match.date)).strip()

    match.team1 = team1
    match.team2 = team2
    match.img_team1 = img_team1
    match.img_team2 = img_team2
    match.img_arena = img_arena
    match.date = date
    match.save()
    return HttpResponse(b"UPDATED", status=200)


@csrf_exempt
@require_POST
def create_link_ajax(request, match_uuid):
    match = get_object_or_404(TicketMatch, uuid=match_uuid)
    vendor = strip_tags(request.POST.get("vendor", "")).strip()
    vendor_link = request.POST.get("vendor_link", "").strip()
    img_vendor = request.POST.get("img_vendor", "").strip()
    try:
        price = int(request.POST.get("price", 0))
    except ValueError:
        price = 0

    if not (vendor and vendor_link and img_vendor and price >= 0):
        return HttpResponse(b"INVALID", status=400)

    TicketLink.objects.create(
        match=match,
        vendor=vendor,
        vendor_link=vendor_link,
        price=price,
        img_vendor=img_vendor,
    )
    return HttpResponse(b"CREATED", status=201)


# ----- Non-AJAX delete endpoints (redirect back) -----
@csrf_exempt
def delete_ticket(request, id):
    match = get_object_or_404(TicketMatch, uuid=id)
    match.delete()
    return HttpResponseRedirect(reverse("ticket:main_view"))


@csrf_exempt
def delete_link(request, id):
    link = get_object_or_404(TicketLink, uuid=id)
    link.delete()
    return HttpResponseRedirect(reverse("ticket:main_view"))


# ----- Show endpoints -----
def show_xml(request):
    objs = []
    for m in TicketMatch.objects.all().order_by("id"):
        objs.append(m)
        objs.extend(list(TicketLink.objects.filter(match=m).order_by("id")))
    xml_data = serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_xml_by_id(request, match_id):
    match = get_object_or_404(TicketMatch, pk=match_id)
    links = TicketLink.objects.filter(match=match).order_by("id")
    objs = [match] + list(links)
    xml_data = serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_xml_by_uuid(request, match_uuid):
    match = get_object_or_404(TicketMatch, uuid=match_uuid)
    links = TicketLink.objects.filter(match=match).order_by("id")
    objs = [match] + list(links)
    xml_data = serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_json(request):
    data = []
    for m in TicketMatch.objects.all().order_by("id"):
        links = TicketLink.objects.filter(match=m).order_by("id")
        data.append(
            {
                "id": m.id,
                "uuid": str(m.uuid),
                "team1": m.team1,
                "team2": m.team2,
                "img_team1": m.img_team1,
                "img_team2": m.img_team2,
                "img_arena": m.img_arena,
                "date": m.date,
                "links": [
                    {
                        "id": l.id,
                        "uuid": str(l.uuid),
                        "vendor": l.vendor,
                        "vendor_link": l.vendor_link,
                        "price": l.price,
                        "img_vendor": l.img_vendor,
                    }
                    for l in links
                ],
            }
        )
    return JsonResponse(data, safe=False)


def show_json_by_id(request, match_id):
    m = get_object_or_404(TicketMatch, pk=match_id)
    links = TicketLink.objects.filter(match=m).order_by("id")
    data = {
        "id": m.id,
        "uuid": str(m.uuid),
        "team1": m.team1,
        "team2": m.team2,
        "img_team1": m.img_team1,
        "img_team2": m.img_team2,
        "img_arena": m.img_arena,
        "date": m.date,
        "links": [
            {
                "id": l.id,
                "uuid": str(l.uuid),
                "vendor": l.vendor,
                "vendor_link": l.vendor_link,
                "price": l.price,
                "img_vendor": l.img_vendor,
            }
            for l in links
        ],
    }
    return JsonResponse(data)


def show_json_by_uuid(request, match_uuid):
    m = get_object_or_404(TicketMatch, uuid=match_uuid)
    links = TicketLink.objects.filter(match=m).order_by("id")
    data = {
        "id": m.id,
        "uuid": str(m.uuid),
        "team1": m.team1,
        "team2": m.team2,
        "img_team1": m.img_team1,
        "img_team2": m.img_team2,
        "img_arena": m.img_arena,
        "date": m.date,
        "links": [
            {
                "id": l.id,
                "uuid": str(l.uuid),
                "vendor": l.vendor,
                "vendor_link": l.vendor_link,
                "price": l.price,
                "img_vendor": l.img_vendor,
            }
            for l in links
        ],
    }
    return JsonResponse(data)
