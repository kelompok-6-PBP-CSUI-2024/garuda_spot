import requests
from django.http import HttpResponse


def proxy_image(request):
    image_url = request.GET.get("url")
    if not image_url:
        return HttpResponse("No URL provided", status=400)

    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return HttpResponse(f"Error fetching image: {exc}", status=500)

    content_type = resp.headers.get("Content-Type", "image/jpeg")
    return HttpResponse(resp.content, content_type=content_type)
