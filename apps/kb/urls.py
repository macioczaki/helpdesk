from django.urls import path

from . import views

app_name = "kb"

urlpatterns = [
    path("", views.ArticleListView.as_view(), name="list"),
    path("nowy/", views.ArticleCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.ArticleDetailView.as_view(), name="detail"),
    path("<slug:slug>/edytuj/", views.ArticleUpdateView.as_view(), name="update"),
]
