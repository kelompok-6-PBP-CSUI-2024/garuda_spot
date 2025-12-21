from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login-mobile/", views.login_mobile, name="login_mobile"),
    path("register/", views.register_view, name="register"),
    path("logout/", LogoutView.as_view(next_page="news:show_main"), name="logout"),
    path("logout-mobile/", views.logout_mobile, name="logout_mobile"),
]
