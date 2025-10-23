from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core import serializers

from .models import TicketMatch, TicketLink


def main_view(request):
    return render(request, "tickets_main.html")


def create_ticket(request):
    pass


def edit_ticket(request, id):
    pass


def delete_ticket(request, id):
    pass


def create_link(request, match_id):
    pass


def delete_link(request, id):
    pass


def show_xml(request):
    # Order as: each TicketMatch followed by its TicketLinks
    objs = []
    for m in TicketMatch.objects.all().order_by("id"):
        objs.append(m)
        objs.extend(list(TicketLink.objects.filter(match=m).order_by("id")))
    xml_data = serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")

def show_xml_by_uuid(request, match_id):
    match = get_object_or_404(TicketMatch, match_id=match_id)
    links = TicketLink.objects.filter(match=match)
    objs = [match] + list(links)
    xml_data = serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_json(request):
    # Nested per match to align with tickets_main.html
    data = []
    for m in TicketMatch.objects.all().order_by("id"):
        links = TicketLink.objects.filter(match=m).order_by("id")
        data.append(
            {
                "id": m.id,
                "uuid": str(m.match_id),
                "team1": m.team1,
                "team2": m.team2,
                "img_team1": m.img_team1,
                "img_team2": m.img_team2,
                "img_arena": m.img_arena,
                "date": m.date,
                "links": [
                    {
                        "uuid": str(l.link_id),
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


def show_json_by_uuid(request, match_id):
    m = get_object_or_404(TicketMatch, match_id=match_id)
    links = TicketLink.objects.filter(match=m).order_by("id")
    data = {
        "uuid": str(m.match_id),
        "team1": m.team1,
        "team2": m.team2,
        "img_team1": m.img_team1,
        "img_team2": m.img_team2,
        "img_arena": m.img_arena,
        "date": m.date,
        "links": [
            {
                "uuid": str(l.link_id),
                "vendor": l.vendor,
                "vendor_link": l.vendor_link,
                "price": l.price,
                "img_vendor": l.img_vendor,
            }
            for l in links
        ],
    }
    return JsonResponse(data)
