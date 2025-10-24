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

from .forms import NewsForm
from .models import News
from datetime import datetime
import re

MONTH_MAP = {
    "jan":1,"januari":1,"feb":2,"februari":2,"mar":3,"maret":3,"apr":4,"april":4,
    "mei":5,"may":5,"jun":6,"juni":6,"jul":7,"juli":7,"agu":8,"agustus":8,"aug":8,"august":8,
    "sep":9,"september":9,"okt":10,"oct":10,"oktober":10,"october":10,"nov":11,"november":11,
    "des":12,"dec":12,"desember":12,"december":12,
}
def _extract_month(s: str):
    if not s: return None
    m = re.search(r"\d{1,2}\s+([A-Za-zÀ-ÿ\.]+)\s+20\d{2}", s) or \
        re.search(r"\b([A-Za-zÀ-ÿ\.]+)\b\s+20\d{2}", s)
    if not m: return None
    return MONTH_MAP.get(m.group(1).lower().strip("."))


def _parse_dt_for_sort(s: str) -> datetime | None:
    """
    Accepts strings like:
    'Kamis, 09 Okt 2025 13:40 WIB' or '09 Okt 2025 13:40', etc.
    Returns a datetime or None if it can’t be parsed.
    """
    if not s:
        return None
    s = re.sub(r"^[A-Za-zÀ-ÿ]+,\s*", "", s.strip())
    m = re.search(r"(\d{1,2})\s+([A-Za-zÀ-ÿ\.]+|\d{1,2})\s+(20\d{2})(?:\s+(\d{1,2}):(\d{2}))?", s)
    if not m:
        return None
    d, mon_s, y, hh, mm = m.groups()
    try:
        mon = int(mon_s)
    except ValueError:
        mon = MONTH_MAP.get(mon_s.lower().strip("."), None)
    if not mon:
        return None
    h = int(hh) if hh else 0
    mi = int(mm) if mm else 0
    try:
        return datetime(int(y), int(mon), int(d), h, mi)
    except Exception:
        return None



def show_main(request):
    return render(request, "main.html")

@login_required
def show_news(request, id):
    news = get_object_or_404(News, pk=id)
    return render(request, "news_detail.html", {"news": news})


@login_required
def create_news(request):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    form = NewsForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('news:show_main')
    return render(request, "create_news.html", {"form": form})

@login_required
def edit_news(request, id):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    news = get_object_or_404(News, pk=id)
    form = NewsForm(request.POST or None, instance=news)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('news:show_news', id=news.id)
    return render(request, "edit_news.html", {"form": form})


@login_required
def delete_news(request, id):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    news = get_object_or_404(News, pk=id)
    news.delete()
    return HttpResponseRedirect(reverse('news:show_main'))

def show_xml(request):
    xml_data = serializers.serialize("xml", News.objects.all())
    return HttpResponse(xml_data, content_type="application/xml")

from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.http import require_GET

@require_GET
def show_json(request):
    month = request.GET.get("month")
    sort_order = (request.GET.get("sort") or "desc").lower()
    sort_reverse = False if sort_order == "asc" else True

    qs = News.objects.all()
    if month and month.isdigit():
        qs = qs.filter(published_month=int(month))

    items = list(qs.values("id", "title", "category", "publish_date", "content"))

    for x in items:
        x["_ts"] = _parse_dt_for_sort(x.get("publish_date", "")) or datetime.min

    items.sort(key=lambda x: x["_ts"], reverse=sort_reverse)

    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get("page_size", 20))
    except ValueError:
        page_size = 20
    page_size = max(1, min(page_size, 100))

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    for x in page_items:
        x.pop("_ts", None)

    return JsonResponse({
        "items": page_items,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "total": total,
    })


def show_xml_by_id(request, news_id):
    qs = News.objects.filter(pk=news_id)
    xml_data = serializers.serialize("xml", qs)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json_by_id(request, news_id):
    try:
        n = News.objects.get(pk=news_id)
    except News.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)
    data = {
        "id": str(n.id),
        "title": n.title,
        "category": n.category,
        "publish_date": n.publish_date,
        "content": n.content,
    }
    return JsonResponse(data)

@login_required
@require_POST
def add_news_entry_ajax(request):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")

    title = strip_tags(request.POST.get("title", "")).strip()
    category = strip_tags(request.POST.get("category", "")).strip()
    publish_date = strip_tags(request.POST.get("publish_date", "")).strip()
    content = strip_tags(request.POST.get("content", ""))

    if not (title and category and content):
        return JsonResponse({"error": "title, category, content are required"}, status=400)

    publish_date = strip_tags(request.POST.get("publish_date", "")).strip()
    n = News.objects.create(
        title=title,
        category=category,
        publish_date=publish_date,
        published_month=_extract_month(publish_date),
        content=content,
    )
    return JsonResponse(
        {
            "id": str(n.id),
            "title": n.title,
            "category": n.category,
            "publish_date": n.publish_date,
            "content": n.content,
        },
        status=201,
    )

@login_required
@require_POST
def delete_news_ajax(request, id):
    if not getattr(request.user, "is_admin", False):
        return HttpResponseForbidden("Admins only")
    obj = get_object_or_404(News, pk=id)
    obj.delete()
    return JsonResponse({"deleted": str(id)})
