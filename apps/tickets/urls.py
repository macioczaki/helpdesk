from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.TicketListView.as_view(), name="list"),
    path("nowe/", views.TicketCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TicketDetailView.as_view(), name="detail"),
    path("<int:pk>/edytuj/", views.TicketUpdateView.as_view(), name="update"),
    path("<int:pk>/komentarz/", views.ticket_add_comment, name="add_comment"),
    path("zalacznik/<int:pk>/", views.attachment_download, name="attachment_download"),
]