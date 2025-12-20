import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core import serializers as django_serializers
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

from .models import TicketMatch, TicketLink
from .forms import TicketMatchForm, TicketLinkForm
from .serializers import (
    parse_link_payload,
    parse_match_payload,
    serialize_match,
)


def _is_admin_user(request) -> bool:
    return request.user.is_authenticated and (getattr(request.user, "is_admin", False) or request.user.is_superuser)


def _get_payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            body = request.body.decode()
        except (AttributeError, UnicodeDecodeError):
            return None
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return request.POST.dict()


def main_view(request):
    return render(request, "tickets_main.html", {"user": request.user})


# ----- Forms (HTML fragments for modals) -----
def form_match(request, match_uuid=None):
    if not _is_admin_user(request):
        return HttpResponse("FORBIDDEN", status=403)
    instance = None
    if match_uuid:
        instance = get_object_or_404(TicketMatch, match_id=match_uuid)
    return render(request, "gen_tick_match.html", {"match": instance})


def form_link(request, match_uuid):
    if not _is_admin_user(request):
        return HttpResponse("FORBIDDEN", status=403)
    match = get_object_or_404(TicketMatch, match_id=match_uuid)
    return render(request, "gen_tick_link.html", {"match": match})


# ----- AJAX endpoints for create/update -----
@csrf_exempt
@require_POST
def create_ticket_ajax(request):
    if not _is_admin_user(request):
        return HttpResponse(b"FORBIDDEN", status=403)
    payload = _get_payload(request)
    if payload is None:
        return HttpResponseBadRequest(b"INVALID_JSON")
    form = TicketMatchForm(parse_match_payload(payload))
    if form.is_valid():
        form.save()
        return HttpResponse(b"CREATED", status=201)
    return HttpResponse(b"INVALID", status=400)


@csrf_exempt
@require_POST
def edit_ticket_ajax(request, id):
    if not _is_admin_user(request):
        return HttpResponse(b"FORBIDDEN", status=403)
    match = get_object_or_404(TicketMatch, match_id=id)
    payload = _get_payload(request)
    if payload is None:
        return HttpResponseBadRequest(b"INVALID_JSON")
    form = TicketMatchForm(parse_match_payload(payload), instance=match)
    if form.is_valid():
        form.save()
        return HttpResponse(b"UPDATED", status=200)
    return HttpResponse(b"INVALID", status=400)


@csrf_exempt
@require_POST
def create_link_ajax(request, match_uuid):
    if not _is_admin_user(request):
        return HttpResponse(b"FORBIDDEN", status=403)
    match = get_object_or_404(TicketMatch, match_id=match_uuid)
    payload = _get_payload(request)
    if payload is None:
        return HttpResponseBadRequest(b"INVALID_JSON")
    form = TicketLinkForm(parse_link_payload(payload))
    if form.is_valid():
        link = form.save(commit=False)
        link.match = match
        link.save()
        return HttpResponse(b"CREATED", status=201)
    return HttpResponse(b"INVALID", status=400)


# ----- Non-AJAX delete endpoints (redirect back) -----
@csrf_exempt
def delete_ticket(request, id):
    if not _is_admin_user(request):
        return HttpResponse(b"FORBIDDEN", status=403)
    match = get_object_or_404(TicketMatch, match_id=id)
    match.delete()
    return HttpResponseRedirect(reverse("tickets:main_view"))


@csrf_exempt
def delete_link(request, id):
    if not _is_admin_user(request):
        return HttpResponse(b"FORBIDDEN", status=403)
    link = get_object_or_404(TicketLink, link_id=id)
    link.delete()
    return HttpResponseRedirect(reverse("tickets:main_view"))


def ticket_detail(request, match_uuid):
    match = get_object_or_404(TicketMatch, match_id=match_uuid)
    links = TicketLink.objects.filter(match=match).order_by("id")
    return render(request, "ticket_detail.html", {"match": match, "links": links, "user": request.user})


# ----- Show endpoints -----
def show_xml(request):
    objs = []
    for m in TicketMatch.objects.all().order_by("id"):
        objs.append(m)
        objs.extend(list(TicketLink.objects.filter(match=m).order_by("id")))
    xml_data = django_serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_xml_by_id(request, match_id):
    match = get_object_or_404(TicketMatch, pk=match_id)
    links = TicketLink.objects.filter(match=match).order_by("id")
    objs = [match] + list(links)
    xml_data = django_serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_xml_by_uuid(request, match_uuid):
    match = get_object_or_404(TicketMatch, match_id=match_uuid)
    links = TicketLink.objects.filter(match=match).order_by("id")
    objs = [match] + list(links)
    xml_data = django_serializers.serialize("xml", objs)
    return HttpResponse(xml_data, content_type="application/xml")


def show_json(request):
    matches = TicketMatch.objects.all().order_by("id").prefetch_related("links")
    data = [serialize_match(m) for m in matches]
    return JsonResponse(data, safe=False)


def show_json_by_id(request, match_id):
    m = (
        TicketMatch.objects.filter(pk=match_id)
        .prefetch_related("links")
        .first()
        or get_object_or_404(TicketMatch, pk=match_id)
    )
    return JsonResponse(serialize_match(m))


def show_json_by_uuid(request, match_uuid):
    m = (
        TicketMatch.objects.filter(match_id=match_uuid)
        .prefetch_related("links")
        .first()
        or get_object_or_404(TicketMatch, match_id=match_uuid)
    )
    return JsonResponse(serialize_match(m))
