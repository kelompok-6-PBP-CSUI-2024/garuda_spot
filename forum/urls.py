from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("partial/", views.post_list_partial, name="post_list_partial"),
    path("create/", views.post_create, name="post_create"),

    path("forum/<slug:slug>/", views.post_detail, name="post_detail"),
    path("<slug:slug>/comment/", views.comment_create, name="comment_create"),
    path("<slug:slug>/like/", views.post_like, name="post_like"),

    # WEB delete (ADMIN ONLY)
    path("comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("post/<slug:slug>/delete/", views.delete_post, name="delete_post"),

    # API (Flutter)
    path("api/posts/", views.api_posts, name="api_posts"),
    path("api/posts/<slug:slug>/", views.api_post_detail, name="api_post_detail"),
    path("api/posts/<slug:slug>/like/", views.api_toggle_like, name="api_toggle_like"),

    # API delete (ADMIN ONLY)
    path("api/posts/<slug:slug>/delete/", views.api_delete_post, name="api_delete_post"),
    path("api/comments/<int:comment_id>/delete/", views.api_delete_comment, name="api_delete_comment"),
]
