from django.shortcuts import render, get_object_or_404
from merch.models import Merch
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils.html import strip_tags


ALLOWED_CATEGORIES = {"cap", "hoodie", "jacket", "jersey", "keychain", "scarf", "others"}

def to_int(val, default=0):
    try:
        v = int(val)
    except (TypeError, ValueError):
        return default
    return max(0, v)

@ensure_csrf_cookie
@login_required
def show_merch(request):
    filter_type = request.GET.get("filter", "all")
    all_merch = Merch.objects.all()
    if filter_type in ALLOWED_CATEGORIES:
        all_merch = all_merch.filter(category=filter_type)

    context = {
        "name": request.user.username,
        "list_merch": all_merch,
    }
    return render(request, "merch_main.html", context)

@login_required
@require_http_methods(["POST"])
def create_merch(request):

    name = strip_tags(request.POST.get("name", "")).strip()
    vendor = strip_tags(request.POST.get("vendor", "")).strip()
    description = strip_tags(request.POST.get("description", "")).strip()
    thumbnail = (request.POST.get("thumbnail") or "").strip()
    category = (request.POST.get("category") or "").strip().lower()
    link = (request.POST.get("link") or "").strip()

    price = to_int(request.POST.get("price"), 0)
    stock = to_int(request.POST.get("stock"), 0)

    if not name:
        return HttpResponseBadRequest("Field 'name' is required")
    if not vendor:
        return HttpResponseBadRequest("Field 'vendor' is required")
    if category not in ALLOWED_CATEGORIES:
        category = "others"

    merch = Merch(
        name=name,
        vendor=vendor,
        price=price,
        stock=stock,
        description=description,
        thumbnail=thumbnail,
        category=category,
        link=link,
    )
    merch.save()

    data = {
        "id": merch.id,
        "name": merch.name,
        "vendor": merch.vendor,
        "price": merch.price,
        "stock": merch.stock,
        "description": merch.description,
        "thumbnail": merch.thumbnail,
        "category": merch.category,
        "link": merch.link,
    }
    return JsonResponse(data, status=201)

@login_required
@require_http_methods(["POST", "PUT", "PATCH"])
def update_merch(request, id):
    try:
        merch = Merch.objects.get(pk=id)
    except Merch.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)

    if "name" in request.POST:
        merch.name = strip_tags(request.POST.get("name", merch.name)).strip()
    if "vendor" in request.POST:
        merch.vendor = strip_tags(request.POST.get("vendor", merch.vendor)).strip()
    if "description" in request.POST:
        merch.description = strip_tags(request.POST.get("description", merch.description)).strip()
    if "thumbnail" in request.POST:
        merch.thumbnail = (request.POST.get("thumbnail") or merch.thumbnail).strip()
    if "link" in request.POST:                                   # << added
        merch.link = (request.POST.get("link") or merch.link).strip()

    if "price" in request.POST:
        new_price = to_int(request.POST.get("price"), merch.price)
        if new_price is not None:
            merch.price = new_price
    if "stock" in request.POST:
        new_stock = to_int(request.POST.get("stock"), merch.stock)
        if new_stock is not None:
            merch.stock = new_stock

    if "category" in request.POST:
        cat = (request.POST.get("category") or merch.category).strip().lower()
        if cat in ALLOWED_CATEGORIES:
            merch.category = cat

    merch.save()

    data = {
        "id": merch.id,
        "name": merch.name,
        "vendor": merch.vendor,
        "price": merch.price,
        "stock": merch.stock,
        "description": merch.description,
        "thumbnail": merch.thumbnail,
        "category": merch.category,
        "link": merch.link,
    }
    return JsonResponse(data)

def detail(request, id):
    merch = get_object_or_404(Merch, pk=id)

    context = {
        'merch': merch
    }

    return render(request, "merch_detail.html", context)

@login_required
def delete_merch(request, id):
    if request.method not in ("POST", "DELETE"):
        return HttpResponseNotAllowed(["POST", "DELETE"])

    if not getattr(request.user, "is_admin", False):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    merch = get_object_or_404(Merch, pk=id)
    merch.delete()
    return JsonResponse({"deleted": id}, status=200)

def show_json(request):
    list_merch = Merch.objects.all()
    data = [
        {
            'id' : merch.id,
            'name': merch.name,
            'vendor': merch.vendor,
            'price': merch.price,
            'stock' : merch.stock,
            'description': merch.description,
            'thumbnail': merch.thumbnail,
            'category': merch.category,
            'link': merch.link,
        }
        for merch in list_merch
    ]
    return JsonResponse(data, safe=False)

def show_json_by_id(request, product_id):
    try:
        merch = Merch.objects.select_related('user').get(pk=product_id)
        data = {
            'id': merch.id,
            'name': merch.name,
            'vendor': merch.vendor,
            'price': merch.price,
            'stock' : merch.stock,
            'description': merch.description,
            'thumbnail': merch.thumbnail,
            'category': merch.category,
            'link': merch.link,
            'user_username': merch.user.username if merch.user_id else None,
        }
        return JsonResponse(data)
    except Merch.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)
