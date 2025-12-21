import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, Paginator
from django.db.models import F
from django.http import (
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import CommentForm, PostFilterForm, PostForm
from .models import Category, Comment, Like, Post


# Helpers
def _is_admin(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def ensure_default_categories():
    defaults = ["Match", "Merch", "News", "Player", "Ticket"]
    for name in defaults:
        Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})


def _get_posts_context(request):
    active_category = request.GET.get("category", "all")

    qs = Post.objects.select_related("category").filter(status=Post.PUBLISHED).order_by(
        "-created_at"
    )
    if active_category and active_category != "all":
        qs = qs.filter(category__slug=active_category)

    paginator = Paginator(qs, 6)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    # liked_ids sekarang dari DB Like (bukan session)
    page_posts = list(page_obj.object_list)
    liked_ids = set(
        Like.objects.filter(user=request.user, post__in=page_posts).values_list(
            "post_id", flat=True
        )
    )

    return {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "active_category": active_category or "all",
        "liked_ids": liked_ids,
        "is_admin": request.user.is_superuser,
    }


# WEB pages (template)
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
            "active_category": post.category.slug if post.category_id else "all",
            "is_admin": request.user.is_superuser,
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
        # kalau form belum set author_name, isi dari user
        if not getattr(comment, "author_name", ""):
            comment.author_name = request.user.username
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
    """WEB toggle like (template) - sekarang per-user via DB Like."""
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)

    existing = Like.objects.filter(post=post, user=request.user).first()
    if existing:
        existing.delete()
        liked = False
    else:
        Like.objects.create(post=post, user=request.user)
        liked = True

    # sync like_count biar field existing tetap dipakai
    new_count = Like.objects.filter(post=post).count()
    Post.objects.filter(pk=post.pk).update(like_count=new_count)
    post.refresh_from_db(fields=["like_count"])

    return JsonResponse({"ok": True, "liked": liked, "like_count": post.like_count})


# WEB delete: SUPERUSER ONLY
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


# JSON / Flutter
def serialize_post(post, request=None):
    created = post.created_at
    if created is not None:
        created_local = timezone.localtime(created)
        date_str = created_local.strftime("%A, %d %B %Y • %H:%M")
    else:
        date_str = ""

    category_name = post.category.name if post.category_id else ""
    author_name = post.author_name or ""

    is_liked = False
    if request is not None and request.user.is_authenticated:
        is_liked = Like.objects.filter(post=post, user=request.user).exists()

    return {
        "id": post.pk,
        "slug": post.slug,
        "title": post.title,
        "content": post.body,
        "category": category_name,
        "author": author_name,
        "date": date_str,
        "like_count": post.like_count,
        "is_liked": is_liked,
    }


@require_GET
@login_required
def api_post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("category"),
        slug=slug,
        status=Post.PUBLISHED,
    )

    post_data = serialize_post(post, request=request)

    comments_qs = post.comments.all().order_by("created_at")
    comments_data = []
    for c in comments_qs:
        created = c.created_at
        if created is not None:
            created_local = timezone.localtime(created)
            time_str = created_local.strftime("%d %b %Y %H:%M")
        else:
            time_str = ""

        comments_data.append(
            {
                "id": c.pk,
                "author": c.author_name,
                "content": c.body,
                "time": time_str,
            }
        )

    return JsonResponse({"post": post_data, "comments": comments_data})


@csrf_exempt
@login_required
def api_posts(request):
    # GET: list
    if request.method == "GET":
        ensure_default_categories()
        qs = (
            Post.objects.select_related("category")
            .filter(status=Post.PUBLISHED)
            .order_by("-created_at")
        )
        data = [serialize_post(p, request=request) for p in qs]
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

        # jangan percaya author dari client, ambil dari user login
        author_name = request.user.username

        if not title or not content:
            return JsonResponse({"error": "Title dan content wajib diisi"}, status=400)

        ensure_default_categories()

        category = None
        if category_name:
            category = Category.objects.filter(name__iexact=category_name).first()
        if category is None:
            category = Category.objects.filter(name__iexact="News").first()

        post = Post.objects.create(
            title=title,
            body=content,
            category=category,
            author_name=author_name,
            status=Post.PUBLISHED,
        )
        return JsonResponse(serialize_post(post, request=request), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@login_required
def api_toggle_like(request, slug):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)

    existing = Like.objects.filter(post=post, user=request.user).first()
    if existing:
        existing.delete()
        liked = False
    else:
        Like.objects.create(post=post, user=request.user)
        liked = True

    new_count = Like.objects.filter(post=post).count()
    Post.objects.filter(pk=post.pk).update(like_count=new_count)
    post.refresh_from_db(fields=["like_count"])

    return JsonResponse({"liked": liked, "like_count": post.like_count})


@csrf_exempt
@login_required
@require_POST
def api_create_comment(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.PUBLISHED)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    content = (body.get("content") or "").strip()
    if not content:
        return JsonResponse({"error": "Content wajib diisi"}, status=400)

    comment = Comment.objects.create(
        post=post,
        author_name=request.user.username,
        body=content,
    )

    created_local = timezone.localtime(comment.created_at) if comment.created_at else None
    time_str = created_local.strftime("%d %b %Y %H:%M") if created_local else ""

    return JsonResponse(
        {
            "id": comment.pk,
            "author": comment.author_name,
            "content": comment.body,
            "time": time_str,
        },
        status=201,
    )


# API delete: SUPERUSER ONLY

@csrf_exempt
@login_required
@require_POST
def api_delete_post(request, slug):
    if not _is_admin(request.user):
        return JsonResponse({"error": "Forbidden", "detail": "Superuser only"}, status=403)

    post = get_object_or_404(Post, slug=slug)
    post.delete()
    return JsonResponse({"ok": True})

@csrf_exempt
@login_required
@require_POST
def api_delete_comment(request, comment_id):
    if not _is_admin(request.user):
        return JsonResponse({"error": "Forbidden", "detail": "Superuser only"}, status=403)

    c = get_object_or_404(Comment, id=comment_id)
    c.delete()
    return JsonResponse({"ok": True})
