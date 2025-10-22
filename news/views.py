from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

from .forms import NewsForm
from .models import News

def show_main(request):
    news_list = News.objects.all()
    return render(request, "main.html", {"news_list": news_list})

def create_news(request):
    form = NewsForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('news:show_main')
    return render(request, "create_news.html", {"form": form})

def show_news(request, id):
    news = get_object_or_404(News, pk=id)
    return render(request, "news_detail.html", {"news": news})

def edit_news(request, id):
    news = get_object_or_404(News, pk=id)
    form = NewsForm(request.POST or None, instance=news)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('news:show_news', id=news.id)
    return render(request, "edit_news.html", {"form": form})

def delete_news(request, id):
    news = get_object_or_404(News, pk=id)
    news.delete()
    return HttpResponseRedirect(reverse('news:show_main'))


def show_xml(request):
    xml_data = serializers.serialize("xml", News.objects.all())
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    data = [
        {
            "id": str(n.id),
            "title": n.title,
            "category": n.category,
            "publish_date": n.publish_date,  # raw string
            "content": n.content,
        }
        for n in News.objects.all()
    ]
    return JsonResponse(data, safe=False)

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

@csrf_exempt
@require_POST
def add_news_entry_ajax(request):
    title = strip_tags(request.POST.get("title", "")).strip()
    category = strip_tags(request.POST.get("category", "")).strip()
    publish_date = strip_tags(request.POST.get("publish_date", "")).strip()
    content = strip_tags(request.POST.get("content", ""))

    if not (title and category and content):
        return HttpResponse(b"INVALID", status=400)

    News.objects.create(
        title=title,
        category=category,
        publish_date=publish_date,
        content=content,
    )
    return HttpResponse(b"CREATED", status=201)
