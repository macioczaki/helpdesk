from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("", views.AssetListView.as_view(), name="list"),
    path("nowy/", views.AssetCreateView.as_view(), name="create"),
    path("<int:pk>/qr/", views.asset_qr, name="qr"),
    path("<int:pk>/", views.AssetDetailView.as_view(), name="detail"),
    path("<int:pk>/edytuj/", views.AssetUpdateView.as_view(), name="update"),
    path("<int:pk>/przypisz/", views.asset_assign, name="assign"),

    path("licencje/", views.LicenseListView.as_view(), name="license_list"),
    path("licencje/nowa/", views.LicenseCreateView.as_view(), name="license_create"),
    path("licencje/<int:pk>/edytuj/", views.LicenseUpdateView.as_view(), name="license_update"),
]