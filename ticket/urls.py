from django.urls import path
from .views import (
    main_view,
    create_ticket, edit_ticket, delete_ticket,
    create_link, delete_link,
    show_xml, show_xml_by_uuid,
    show_json, show_json_by_uuid,
)

app_name = "ticket"

urlpatterns = [
    path("", main_view, name="main_view"),

    path("create/", create_ticket, name="create_ticket"),
    path("edit/<uuid:match_id>/", edit_ticket, name="edit_ticket"),
    path("delete/<uuid:match_id>/", delete_ticket, name="delete_ticket"),

    path("link/create/<uuid:match_id>/", create_link, name="create_link"),
    path("link/delete/<uuid:link_id>/", delete_link, name="delete_link"),

    path("xml/", show_xml, name="show_xml"),
    path("xml/<uuid:match_id>/", show_xml_by_uuid, name="show_xml_by_uuid"),
    path("json/", show_json, name="show_json"),
    path("json/<uuid:match_id>/", show_json_by_uuid, name="show_json_by_uuid"),
]
