from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    return render(request, "accounts/home.html")


@login_required
def profile(request):
    return render(request, "accounts/profile.html")