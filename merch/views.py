from django.shortcuts import render, get_object_or_404
from merch.models import Merch
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils.html import strip_tags

@ensure_csrf_cookie
@login_required
def show_merch(request):
    list_merch = Merch.objects.all()
    filter_type = request.GET.get("filter", "all")
    
    if filter_type in ['keychain','jersey','jacket','hoodie','cap','scarf']:
        filter_type = filter_type.filter(category=filter_type)

    context = {
        'name': request.user.username,
        'list_merch': list_merch,
    }
    return render(request, "merch_main.html", context)

@login_required
@require_http_methods(["POST"])
def create_merch(request):
    name = strip_tags(request.POST.get('name', '')).strip()
    description = strip_tags(request.POST.get('description', '')).strip()

    merch = Merch(
        name=name,
        description=description,
        price=request.POST.get('price') or 0,
        stock=request.POST.get('stock') or 0,
        thumbnail=request.POST.get('thumbnail') or '',
        category=request.POST.get('category') or '',
        user=request.user,
    )
    merch.save()

    data = {
        'id': merch.id,
        'name': merch.name,
        'price': merch.price,
        'stock': merch.stock,
        'description': merch.description,
        'thumbnail': merch.thumbnail,
        'category': merch.category,
        'user_id': merch.user_id,
    }
    return JsonResponse(data, status=201)

@login_required
@require_http_methods(["POST", "PUT", "PATCH"])
def update_merch(request, id):
    try:
        merch = Merch.objects.get(pk=id)
    except Merch.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

    if 'name' not in request.POST:
        return HttpResponseBadRequest("Invalid payload")

    merch.name = strip_tags(request.POST.get('name', merch.name)).strip()
    merch.description = strip_tags(request.POST.get('description', merch.description)).strip()
    if 'price' in request.POST: merch.price = request.POST.get('price') or merch.price
    if 'stock' in request.POST: merch.stock = request.POST.get('stock') or merch.stock
    if 'thumbnail' in request.POST: merch.thumbnail = request.POST.get('thumbnail') or merch.thumbnail
    if 'category' in request.POST: merch.category = request.POST.get('category') or merch.category
    merch.save()

    data = {
        'id': merch.id,
        'name': merch.name,
        'price': merch.price,
        'stock': merch.stock,
        'description': merch.description,
        'thumbnail': merch.thumbnail,
        'category': merch.category,
        'user_id': merch.user_id,
    }
    return JsonResponse(data)

def detail(request, id):
    merch = get_object_or_404(Merch, pk=id)

    context = {
        'merch': merch
    }

    return render(request, "detail_merch.html", context)

@login_required
@require_http_methods(["POST", "DELETE"])
def delete_merch(request, id):
    try:
        merch = Merch.objects.get(pk=id)
    except Merch.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)
    merch.delete()
    return HttpResponse(status=204)

def show_json(request):
    list_merch = Merch.objects.all()
    data = [
        {
            'id' : merch.id,
            'name': merch.name,
            'price': merch.price,
            'stock' : merch.stock,
            'description': merch.description,
            'thumbnail': merch.thumbnail,
            'category': merch.category,
            'user_id': merch.user_id,
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
            'price': merch.price,
            'stock' : merch.stock,
            'description': merch.description,
            'thumbnail': merch.thumbnail,
            'category': merch.category,
            'user_id': merch.user_id,
            'user_username': merch.user.username if merch.user_id else None,
        }
        return JsonResponse(data)
    except Merch.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)