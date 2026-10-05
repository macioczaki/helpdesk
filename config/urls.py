from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path


def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),

    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", include("apps.accounts.urls")),

    path("zgloszenia/", include("apps.tickets.urls")),
    path("raporty/", include("apps.reports.urls")),
    path("majatek/", include("apps.assets.urls")),
]