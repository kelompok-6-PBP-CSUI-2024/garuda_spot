# forum/views.py
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.db.models import F
from .models import Post, Category
from .forms import PostFilterForm, PostForm, CommentForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def post_list(request):
    categories = Category.objects.all()
    base_ctx = {
        "categories": categories,
        "active_category": request.GET.get("category", "all"),
        "year": timezone.now().year,
        "post_form": PostForm(),
    }
    base_ctx.update(_get_posts_context(request))
    base_ctx["form"] = PostFilterForm(request.GET or None)
    return render(request, "forum/post_list.html", base_ctx)

@login_required
def post_list_partial(request):
    try:
        ctx = _get_posts_context(request)
    except Http404:
        return JsonResponse({"html": "<p class='muted'>Tidak ada data.</p>", "has_next": False, "page": 1})
    html = render_to_string("forum/post_list.html", {**ctx, "partial": True}, request=request)
    return JsonResponse({"html": html, "has_next": ctx["page_obj"].has_next(), "page": ctx["page_obj"].number})

@login_required
def post_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save()  # slug & excerpt auto dari model.save()
        card_html = render_to_string("forum/_post_card.html", {"p": post}, request=request)
        return JsonResponse({"ok": True, "html": card_html})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@login_required
def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("category"), slug=slug, status=Post.PUBLISHED)
    comments = post.comments.all()
    return render(request, "forum/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": CommentForm(),
        "year": timezone.now().year,
        "categories": Category.objects.all(),
        "active_category": post.category.slug
    })

@login_required
def comment_create(request, slug):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        html = render_to_string("forum/_comment.html", {"c": comment}, request=request)
        return JsonResponse({"ok": True, "html": html})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@login_required
def _get_posts_context(request):
    # Bind form dengan GET; kalau GET kosong, form.is_bound == False
    form = PostFilterForm(request.GET or None)

    # Hanya akses cleaned_data jika bound & valid
    if form.is_bound and form.is_valid():
        params = form.cleaned_data
    else:
        params = {}

    qs = Post.objects.select_related("category").filter(status=Post.PUBLISHED)

    # ---- Filter kategori (aman untuk unbound form) ----
    cat_slug = params.get("category") or request.GET.get("category") or "all"
    active_category = "all"
    if cat_slug and cat_slug != "all":
        qs = qs.filter(category__slug=cat_slug)
        active_category = cat_slug

    # ---- Search (aman untuk unbound form) ----
    q = params.get("q") or request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(body__icontains=q) |
            Q(excerpt__icontains=q)
        )

    # ---- Pagination ----
    paginator = Paginator(qs, 6)
    page = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        # Untuk endpoint AJAX, kita tangani ini di view caller
        raise Http404("No more pages")

    return {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "active_category": active_category or "all",
        "liked_ids": set(request.session.get("liked_posts", [])), 
    }

@login_required
def post_list(request):
    ensure_default_categories()  # <== ADD THIS
    categories = Category.objects.all()
    base_ctx = {
        "categories": categories,
        "active_category": request.GET.get("category", "all"),
        "year": timezone.now().year,
        "post_form": PostForm(),
        "form": PostFilterForm(request.GET or None),
    }
    base_ctx.update(_get_posts_context(request))
    return render(request, "forum/post_list.html", base_ctx)

def ensure_default_categories():
    from .models import Category
    if not Category.objects.exists():
        Category.objects.bulk_create([
            Category(name="News",  slug="news"),
            Category(name="Player", slug="player"),
            Category(name="Merch", slug="merch"),
            Category(name="Ticket", slug="ticket"),
            Category(name="Match", slug="match"),
        ])

@login_required
@require_POST
def post_like(request, slug):
    """
    Toggle like/unlike by session.
    Return: { ok, liked, like_count }
    """
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)

    liked_posts = request.session.get("liked_posts", [])
    if not isinstance(liked_posts, list):
        liked_posts = []

    if post.id in liked_posts:
        # UNLIKE
        Post.objects.filter(pk=post.pk, like_count__gt=0).update(like_count=F("like_count") - 1)
        liked_posts.remove(post.id)
        liked = False
    else:
        # LIKE
        Post.objects.filter(pk=post.pk).update(like_count=F("like_count") + 1)
        liked_posts.append(post.id)
        liked = True

    request.session["liked_posts"] = liked_posts
    request.session.modified = True

    post.refresh_from_db(fields=["like_count"])
    return JsonResponse({"ok": True, "liked": liked, "like_count": post.like_count})

@login_required
@require_POST
def post_delete(request, slug):
    """
    Hapus satu post. Hanya untuk user staff/superuser.
    Mendukung AJAX (JSON) dan non-AJAX (redirect + messages).
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        # AJAX -> 403 JSON, non-AJAX -> 403 halaman
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
        return HttpResponseForbidden("Forbidden")

    post = get_object_or_404(Post, slug=slug)

    # Bersihkan jejak like di session (opsional)
    liked_posts = request.session.get("liked_posts", [])
    if isinstance(liked_posts, list) and post.id in liked_posts:
        liked_posts.remove(post.id)
        request.session["liked_posts"] = liked_posts
        request.session.modified = True

    post.delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})

    messages.success(request, "Post berhasil dihapus.")
    return redirect("forum:post_list")