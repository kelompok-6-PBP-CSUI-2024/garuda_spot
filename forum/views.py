from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required

from .models import Post, Category, Comment
from .forms import PostFilterForm, PostForm, CommentForm

import json


def ensure_default_categories():
    if not Category.objects.exists():
        Category.objects.bulk_create([
            Category(name="News",  slug="news"),
            Category(name="Player", slug="player"),
            Category(name="Merch", slug="merch"),
            Category(name="Ticket", slug="ticket"),
            Category(name="Match", slug="match"),
        ])


def _is_admin(user) -> bool:
    return user.is_authenticated and user.is_superuser


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

    paginator = Paginator(qs, 6)
    page = request.GET.get("page", 1)

    page_obj = paginator.get_page(page)
    return {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "active_category": active_category or "all",
        "liked_ids": set(request.session.get("liked_posts", [])),
        "is_admin": request.user.is_superuser,  # biar template bisa hide tombol delete
    }


@login_required
def post_list(request):
    ensure_default_categories()
    categories = Category.objects.all()
    base_ctx = {
        "categories": categories,
        "active_category": request.GET.get("category", "all"),
        "year": timezone.now().year,
        "post_form": PostForm(),
        "form": PostFilterForm(request.GET or None),
        "is_admin": request.user.is_superuser,
    }

    try:
        base_ctx.update(_get_posts_context(request))
    except EmptyPage:
        base_ctx.update({"posts": [], "page_obj": None})

    return render(request, "forum/post_list.html", base_ctx)


@login_required
def post_list_partial(request):
    try:
        ctx = _get_posts_context(request)
    except EmptyPage:
        return JsonResponse({"html": "", "has_next": False})

    html_list = []
    for post in ctx.get("posts", []):
        html_list.append(
            render_to_string(
                "forum/_post_card.html",
                {
                    "p": post,
                    "liked_ids": ctx.get("liked_ids", set()),
                    "is_admin": request.user.is_superuser,
                },
                request=request,
            )
        )
    html = "".join(html_list)

    return JsonResponse({"html": html, "has_next": ctx["page_obj"].has_next()})


@login_required
@require_POST
def post_create(request):
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save()
        card_html = render_to_string(
            "forum/_post_card.html",
            {"p": post, "is_admin": request.user.is_superuser},
            request=request,
        )
        return JsonResponse({"ok": True, "html": card_html})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@login_required
def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("category"),
        slug=slug,
        status=Post.PUBLISHED,
    )
    comments = post.comments.all()
    return render(
        request,
        "forum/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_form": CommentForm(),
            "year": timezone.now().year,
            "categories": Category.objects.all(),
            "active_category": post.category.slug,
            "is_admin": request.user.is_superuser,  # hide tombol delete comment
        },
    )


@login_required
@require_POST
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        html = render_to_string(
            "forum/_comment.html",
            {"c": comment, "is_admin": request.user.is_superuser},
            request=request,
        )
        return JsonResponse({"ok": True, "html": html})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


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


# =========================
# WEB delete: ADMIN ONLY
# =========================
@login_required
@require_POST
def delete_comment(request, comment_id):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Anda tidak punya izin untuk menghapus komentar ini.")

    comment = get_object_or_404(Comment, id=comment_id)
    post_slug = comment.post.slug
    comment.delete()
    return redirect("forum:post_detail", slug=post_slug)


@login_required
@require_POST
def delete_post(request, slug):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Anda tidak punya izin untuk menghapus post ini.")

    post = get_object_or_404(Post, slug=slug)
    post.delete()
    return redirect("forum:post_list")


# =========================
# JSON / Flutter
# =========================
def serialize_post(post):
    created = post.created_at
    if created is not None:
        created_local = timezone.localtime(created)
        date_str = created_local.strftime("%A, %d %B %Y • %H:%M")
    else:
        date_str = ""

    category_name = post.category.name if post.category_id else ""
    author_name = post.author_name or ""

    return {
        "id": post.pk,
        "slug": post.slug,
        "title": post.title,
        "content": post.body,
        "category": category_name,
        "author": author_name,
        "date": date_str,
        "like_count": post.like_count,
    }


@require_GET
def api_post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("category"),
        slug=slug,
        status=Post.PUBLISHED,
    )

    post_data = serialize_post(post)

    comments_qs = post.comments.all().order_by("created_at")
    comments_data = []
    for c in comments_qs:
        created = c.created_at
        if created is not None:
            created_local = timezone.localtime(created)
            time_str = created_local.strftime("%d %b %Y %H:%M")
        else:
            time_str = ""

        comments_data.append({
            "id": c.pk,
            "author": c.author_name,
            "content": c.body,
            "time": time_str,
        })

    return JsonResponse({"post": post_data, "comments": comments_data})


@csrf_exempt
def api_posts(request):
    # GET: list
    if request.method == "GET":
        ensure_default_categories()
        qs = (
            Post.objects.select_related("category")
            .filter(status=Post.PUBLISHED)
            .order_by("-created_at")
        )
        data = [serialize_post(p) for p in qs]
        return JsonResponse({"results": data})

    # POST: create
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        title = (body.get("title") or "").strip()
        content = (body.get("content") or "").strip()
        category_name = (body.get("category") or "").strip()

        author_name = (
            body.get("author")
            or body.get("author_name")
            or body.get("username")
            or ""
        ).strip()

        if not title or not content:
            return JsonResponse({"error": "Title dan content wajib diisi"}, status=400)

        ensure_default_categories()

        category = None
        if category_name:
            category = Category.objects.filter(name__iexact=category_name).first()
        if category is None:
            category = Category.objects.filter(name__iexact="News").first()

        if not author_name:
            author_name = "Orang"

        post = Post.objects.create(
            title=title,
            body=content,
            category=category,
            author_name=author_name,
            status=Post.PUBLISHED,
        )
        return JsonResponse(serialize_post(post), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@login_required
def api_toggle_like(request, slug):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

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
    return JsonResponse({"liked": liked, "like_count": post.like_count})


# =========================
# API delete: ADMIN ONLY
# =========================
@csrf_exempt
@login_required
@require_POST
def api_delete_post(request, slug):
    if not _is_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    post = get_object_or_404(Post, slug=slug)
    post.delete()
    return JsonResponse({"ok": True})


@csrf_exempt
@login_required
@require_POST
def api_delete_comment(request, comment_id):
    if not _is_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    c = get_object_or_404(Comment, id=comment_id)
    c.delete()
    return JsonResponse({"ok": True})
