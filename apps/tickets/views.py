from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import User

from .forms import TicketCreateForm, TicketUpdateForm
from .models import Ticket


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = "tickets/list.html"
    context_object_name = "tickets"
    paginate_by = 20

    def get_queryset(self):
        qs = Ticket.objects.select_related("category", "created_by", "assigned_to")
        if not self.request.user.is_technician:
            qs = qs.filter(created_by=self.request.user)
        status = self.request.GET.get("status")
        if status in Ticket.Status.values:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(number__icontains=q) | Q(title__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Ticket.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = "tickets/detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        qs = Ticket.objects.select_related("category", "created_by", "assigned_to")
        if not self.request.user.is_technician:
            qs = qs.filter(created_by=self.request.user)
        return qs


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = "tickets/form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Zgłoszenie zostało utworzone.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tickets:detail", kwargs={"pk": self.object.pk})


class TicketUpdateView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketUpdateForm
    template_name = "tickets/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        qs = Ticket.objects.all()
        if not self.request.user.is_technician:
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not request.user.is_technician:
            if ticket.created_by_id != request.user.id or ticket.status != Ticket.Status.NEW:
                messages.error(request, "Nie możesz edytować tego zgłoszenia.")
                return redirect("tickets:detail", pk=ticket.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Zgłoszenie zostało zaktualizowane.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tickets:detail", kwargs={"pk": self.object.pk})