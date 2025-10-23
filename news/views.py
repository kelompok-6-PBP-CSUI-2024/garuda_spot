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
    qs = News.objects.all().values("id", "title", "category", "publish_date", "content")
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
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({
            "items": [],
            "page": page,
            "page_size": page_size,
            "has_next": False,
            "total": paginator.count,
        })

    return JsonResponse({
        "items": list(page_obj.object_list),
        "page": page,
        "page_size": page_size,
        "has_next": page_obj.has_next(),
        "total": paginator.count,
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

    n = News.objects.create(
        title=title,
        category=category,
        publish_date=publish_date,
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
