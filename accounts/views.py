# accounts/views.py
from django.contrib import messages
from django.contrib.auth import login as auth_login, get_user_model, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

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
    """
    Lightweight JSON login endpoint for mobile/Flutter clients.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"message": "Invalid credentials"}, status=401)

    auth_login(request, user)
    return JsonResponse(
        {
            "message": "Login success",
            "username": user.username,
            "is_admin": getattr(user, "is_admin", False),
            "is_superuser": user.is_superuser,
        }
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
