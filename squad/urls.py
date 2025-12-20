from django.urls import path
from . import views 

app_name = "squad"

urlpatterns = [
    path("", views.index, name="index"),
    path("player/new/", views.player_create, name="player_create"),
    path("player/<int:pk>/edit/", views.player_edit, name="player_edit"),
    path("player/<int:pk>/", views.player_detail, name="player_detail"),
    path("player/form/", views.player_form, name="player_form"),
    path("player/<int:pk>/delete/", views.player_delete, name="player_delete"),
    path("api/players/", views.api_players, name="api_players"),
    path("api/players/<int:pk>/", views.api_player_detail),
    path("api/players/create/", views.api_player_create),
    path("player/<int:pk>/edit/", views.player_edit, name="player_edit"),
    path("api/players/<int:pk>/edit/",views.api_player_update,name="api_player_update",),
    path("api/players/<int:pk>/delete/", views.api_player_delete, name="api_player_delete"),
]
