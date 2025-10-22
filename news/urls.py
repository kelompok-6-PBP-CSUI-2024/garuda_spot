from django.urls import path
from .views import (
    show_main, create_news, show_news, edit_news, delete_news,
    show_json, show_json_by_id, show_xml, show_xml_by_id,
    add_news_entry_ajax, delete_news_ajax
)

app_name = "news"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("create-news/", create_news, name="create_news"),
    path("news/<uuid:id>/", show_news, name="show_news"),
    path("news/<uuid:id>/edit", edit_news, name="edit_news"),
    path("news/<uuid:id>/delete", delete_news, name="delete_news"),

    path("json/", show_json, name="show_json"),
    path("json/<uuid:news_id>/", show_json_by_id, name="show_json_by_id"),
    path("xml/", show_xml, name="show_xml"),
    path("xml/<uuid:news_id>/", show_xml_by_id, name="show_xml_by_id"),

    path("add/", add_news_entry_ajax, name="add_news_entry_ajax"),
    path("<uuid:id>/delete-ajax/", delete_news_ajax, name="delete_news_ajax"),
]
