from django.urls import path
from .views import (
    show_merch, create_merch, update_merch, detail, delete_merch,
    show_json, show_json_by_id,
)

app_name = "merch"

urlpatterns = [
    path("", show_merch, name="show_merch"),
    path("create/", create_merch, name="create_merch"),
    path("<int:id>/update/", update_merch, name="update_merch"),
    path("<int:id>/detail/", detail, name="detail"),
    path("<int:id>/delete/", delete_merch, name="delete_merch"),

    path("json/", show_json, name="show_json"),
    path("json/<int:id>/", show_json_by_id, name="show_json_by_id"),
]
