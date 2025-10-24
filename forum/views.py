# forum/views.py
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q, F
from django.views.decorators.http import require_POST
from .models import Post, Category
from .forms import PostFilterForm, PostForm, CommentForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# FUNGSI UNTUK MEMBUAT KATEGORI DEFAULT (JIKA BELUM ADA)
def ensure_default_categories():
    if not Category.objects.exists():
        Category.objects.bulk_create([
            Category(name="News",  slug="news"),
            Category(name="Player", slug="player"),
            Category(name="Merch", slug="merch"),
            Category(name="Ticket", slug="ticket"),
            Category(name="Match", slug="match"),
        ])

# FUNGSI INTERNAL UNTUK MENGAMBIL POSTS
@login_required
def _get_posts_context(request):
    form = PostFilterForm(request.GET or None)
    params = form.cleaned_data if form.is_bound and form.is_valid() else {}

    qs = Post.objects.select_related("category").filter(status=Post.PUBLISHED)

    cat_slug = params.get("category") or request.GET.get("category") or "all"
    active_category = "all"
    if cat_slug and cat_slug != "all":
        qs = qs.filter(category__slug=cat_slug)
        active_category = cat_slug

    q = params.get("q") or request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(body__icontains=q) |
            Q(excerpt__icontains=q)
        )

    paginator = Paginator(qs, 6) # 6 post per halaman
    page = request.GET.get("page", 1)
    
    # === PERBAIKAN: Try/Except dipindah ke view ===
    # Biarkan view yang memanggil menangani EmptyPage
    page_obj = paginator.get_page(page) # Menggunakan get_page untuk keamanan

    return {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "active_category": active_category or "all",
        "liked_ids": set(request.session.get("liked_posts", [])), 
    }

# VIEW UNTUK HALAMAN UTAMA (FULL LOAD)
# === PERBAIKAN: FUNGSI DUPLIKAT TELAH DIHAPUS ===
@login_required
def post_list(request):
    ensure_default_categories()  # Pastikan kategori ada
    categories = Category.objects.all()
    base_ctx = {
        "categories": categories,
        "active_category": request.GET.get("category", "all"),
        "year": timezone.now().year,
        "post_form": PostForm(),
        "form": PostFilterForm(request.GET or None),
    }
    
    try:
        base_ctx.update(_get_posts_context(request))
    except EmptyPage:
        # Jika halaman pertama kosong (tidak ada post sama sekali)
        base_ctx.update({
            "posts": [],
            "page_obj": None, # Tidak ada page_obj
        })
        
    return render(request, "forum/post_list.html", base_ctx)

# VIEW UNTUK AJAX (LOAD MORE, FILTER, SEARCH)
@login_required
def post_list_partial(request):
    try:
        ctx = _get_posts_context(request)
    except EmptyPage:
        # Jika tidak ada halaman lagi
        return JsonResponse({"html": "", "has_next": False})

    # === PERBAIKAN: Render _post_card.html di dalam loop Python ===
    html_list = []
    for post in ctx.get("posts", []):
        html_list.append(
            render_to_string(
                "forum/_post_card.html",
                {"p": post, "liked_ids": ctx.get("liked_ids", set())},
                request=request
            )
        )
    html = "".join(html_list)
    
    return JsonResponse({
        "html": html, 
        "has_next": ctx["page_obj"].has_next()
    })

# VIEW UNTUK MEMBUAT POST BARU (VIA AJAX)
@login_required
@require_POST
def post_create(request):
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save()
        # Me-render satu card, ini sudah benar
        card_html = render_to_string("forum/_post_card.html", {"p": post}, request=request)
        return JsonResponse({"ok": True, "html": card_html})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

# VIEW UNTUK HALAMAN DETAIL POST
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

# VIEW UNTUK MEMBUAT KOMENTAR BARU (VIA AJAX)
@login_required
@require_POST
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        html = render_to_string("forum/_comment.html", {"c": comment}, request=request)
        return JsonResponse({"ok": True, "html": html})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

# VIEW UNTUK LIKE/UNLIKE POST (VIA AJAX)
@login_required
@require_POST
def post_like(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    liked_posts = request.session.get("liked_posts", [])
    if not isinstance(liked_posts, list):
        liked_posts = []

    if post.id in liked_posts:
        Post.objects.filter(pk=post.pk, like_count__gt=0).update(like_count=F("like_count") - 1)
        liked_posts.remove(post.id)
        liked = False
    else:
        Post.objects.filter(pk=post.pk).update(like_count=F("like_count") + 1)
        liked_posts.append(post.id)
        liked = True

    request.session["liked_posts"] = liked_posts
    request.session.modified = True
    post.refresh_from_db(fields=["like_count"])
    
    return JsonResponse({"ok": True, "liked": liked, "like_count": post.like_count})

# VIEW UNTUK HAPUS POST (AJAX / NON-AJAX)
@login_required
@require_POST
def post_delete(request, slug):
    if not request.user.is_staff:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
        return HttpResponseForbidden("Forbidden")

    post = get_object_or_404(Post, slug=slug)
    
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