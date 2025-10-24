# urls.py

from django.urls import path
from . import views

app_name = "schedule"

urlpatterns = [
    path('', views.show_main, name='show_main'),

    path("match/<uuid:match_id>/", views.show_match, name="show_match"),

    # URL non-AJAX (Biarkan Saja)
    path('edit/<uuid:id>/', views.edit_match, name='edit_match'),
    path('delete/<uuid:id>/', views.delete_match, name='delete_match'),

    # URL Data Feeds
    path('xml/', views.show_xml, name='show_xml'),
    path('json/', views.show_json, name='show_json'),
    path('xml/<uuid:id>/', views.show_xml_by_id, name='show_xml_by_id'),
    path('json/<uuid:id>/', views.show_json_by_id, name='show_json_by_id'),

# URL AJAX CREATE (Mengganti add_match_ajax lama)
    path('add-ajax/', views.create_match_ajax, name='add_match_ajax'), 
    
    # URL AJAX UPDATE (Mengganti update_match_ajax lama)
    path('update-ajax/<uuid:match_id>/', views.update_match_ajax, name='update_match_ajax'),
    
    # URL AJAX DELETE (Mengganti delete_match_ajax lama)
    path('delete-ajax/<uuid:match_id>/', views.delete_match_ajax, name='delete_match_ajax'),
    
    # --- URL BASE (Seperti pada solusi sebelumnya, untuk menghindari NoReverseMatch) ---
    path('update-ajax-base/', views.show_main, name='update_match_base_url'),
    path('delete-ajax-base/', views.show_main, name='delete_match_base_url'),
]