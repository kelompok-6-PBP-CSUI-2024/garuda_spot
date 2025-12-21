from django.urls import path
from . import views

app_name = "schedule"

urlpatterns = [
    # --- Main Views ---
    path('', views.show_main, name='show_main'),
    # views.py: def show_match(request, match_id)
    path("match/<uuid:match_id>/", views.show_match, name="show_match"),
    
    # --- CRUD Standard (Non-AJAX) ---
    path('create/', views.create_match, name='create_match'),
    path('edit/<uuid:id>/', views.edit_match, name='edit_match'),

    path('delete/<uuid:id>/', views.delete_match, name='delete_match'),

    # --- Data Feeds (XML/JSON) ---
    path('xml/', views.show_xml, name='show_xml'),
    path('json/', views.show_json, name='show_json'),
    path('xml/<uuid:id>/', views.show_xml_by_id, name='show_xml_by_id'),
    path('json/<uuid:id>/', views.show_json_by_id, name='show_json_by_id'),

    # --- AJAX Web Views (Session/Cookie Auth) ---
    path('add-ajax/', views.create_match_ajax, name='add_match_ajax'), 
    path('update-ajax/<uuid:match_id>/', views.update_match_ajax, name='update_match_ajax'),
    path('delete-ajax/<uuid:match_id>/', views.delete_match_ajax, name='delete_match_ajax'),
    
    # --- Mobile / API Views (CSRF Exempt) ---
    path("api/match/", views.api_match, name="api_match"),
    path("api/match/add/", views.add_match_mobile, name="add_match_mobile"),
    path("api/match/delete/<uuid:id>/", views.delete_match_mobile, name="delete_match_mobile"),
    path('api/match/edit/<uuid:id>/', views.edit_match_mobile, name='edit_match_mobile'),

    # --- Placeholder Bases (Untuk kebutuhan template JS URL reversing) ---
    path('update-ajax-base/', views.show_main, name='update_match_base_url'),
    path('delete-ajax-base/', views.show_main, name='delete_match_base_url'),
]