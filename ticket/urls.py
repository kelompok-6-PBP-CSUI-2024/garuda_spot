from django.urls import path
from .views import (
    main_view,
    # modal forms
    form_match, form_link,
    # ajax endpoints
    create_ticket_ajax, edit_ticket_ajax, create_link_ajax,
    # deletes
    delete_ticket, delete_link,
    # show endpoints
    show_xml, show_xml_by_id, show_xml_by_uuid,
    show_json, show_json_by_id, show_json_by_uuid,
    ticket_detail,
)

app_name = "tickets"

urlpatterns = [
    path("", main_view, name="main_view"),
    path("detail/<uuid:match_uuid>/", ticket_detail, name="detail"),

    # forms (GET fragments for modals)
    path("form/match/", form_match, name="form_match"),
    path("form/match/<uuid:match_uuid>/", form_match, name="form_match_edit"),
    path("form/link/<uuid:match_uuid>/", form_link, name="form_link"),

    # ajax create/edit
    path("create/", create_ticket_ajax, name="create_ticket"),
    path("edit/<uuid:id>/", edit_ticket_ajax, name="edit_ticket"),
    path("delete/<uuid:id>/", delete_ticket, name="delete_ticket"),

    path("link/create/<uuid:match_uuid>/", create_link_ajax, name="create_link"),
    path("link/delete/<uuid:id>/", delete_link, name="delete_link"),

    path("xml/", show_xml, name="show_xml"),
    path("xml/<int:match_id>/", show_xml_by_id, name="show_xml_by_id"),
    path("xml/<uuid:match_uuid>/", show_xml_by_uuid, name="show_xml_by_uuid"),
    path("json/", show_json, name="show_json"),
    path("json/<int:match_id>/", show_json_by_id, name="show_json_by_id"),
    path("json/<uuid:match_uuid>/", show_json_by_uuid, name="show_json_by_uuid"),
]
