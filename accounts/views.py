# accounts/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json

def login_view(request):
    if request.user.is_authenticated:
        return redirect("news:show_main")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(request.POST.get("next") or reverse("news:show_main"))
    return render(request, "accounts/login.html", {"form": form})

@csrf_exempt
def login_mobile(request):
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            return JsonResponse(
                {
                    "username": user.username,
                    "is_admin": getattr(user, "is_admin", False),
                    "status": True,
                    "message": "Login successful!",
                },
                status=200,
            )
        return JsonResponse(
            {"status": False, "message": "Login failed, account is disabled."},
            status=401,
        )

    return JsonResponse(
        {"status": False, "message": "Login failed, please check your username or password."},
        status=401,
    )

@csrf_exempt
def register_mobile(request):
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "Invalid request method."}, status=400)

    data = json.loads(request.body)
    username = data.get("username")
    password1 = data.get("password1")
    password2 = data.get("password2")

    if password1 != password2:
        return JsonResponse({"status": False, "message": "Passwords do not match."}, status=400)

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        return JsonResponse({"status": False, "message": "Username already exists."}, status=400)

    user = User.objects.create_user(username=username, password=password1)
    user.save()

    return JsonResponse(
        {"username": user.username, "status": "success", "message": "User created successfully!"},
        status=200,
    )

class SimpleSignupForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username",)

def register_view(request):
    if request.method == "POST":
        form = SimpleSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Akun berhasil dibuat. Silakan login.")
            return redirect("accounts:login")
    else:
        form = SimpleSignupForm()
    return render(request, "accounts/register.html", {"form": form})
