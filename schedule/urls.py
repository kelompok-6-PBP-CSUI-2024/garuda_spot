from django.urls import path
from . import views

app_name = "schedule"

urlpatterns = [
    path('', views.show_main, name='show_main'),

    path("match/<uuid:match_id>/", views.show_match, name="show_match"),

    path('edit/<uuid:id>/', views.edit_match, name='edit_match'),
    path('delete/<uuid:id>/', views.delete_match, name='delete_match'),

    path('xml/', views.show_xml, name='show_xml'),
    path('json/', views.show_json, name='show_json'),
    path('xml/<uuid:id>/', views.show_xml_by_id, name='show_xml_by_id'),
    path('json/<uuid:id>/', views.show_json_by_id, name='show_json_by_id'),

    path('add/', views.add_match_ajax, name='add_match_ajax'),
]
