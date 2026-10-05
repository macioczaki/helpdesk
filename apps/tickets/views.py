from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CommentForm, TicketCreateForm, TicketUpdateForm
from .models import Ticket, TicketAttachment


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        comments = self.object.comments.select_related("author").prefetch_related("attachments")
        if not self.request.user.is_technician:
            comments = comments.filter(is_internal=False)
        ctx["comments"] = comments
        ctx["history"] = self.object.history.select_related("changed_by")[:50]
        ctx["comment_form"] = CommentForm(user=self.request.user)
        ctx["can_convert_to_kb"] = self.request.user.is_technician
        return ctx


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("title_hint") or ""
        if q:
            from apps.kb.models import KnowledgeArticle

            ctx["suggested_articles"] = KnowledgeArticle.objects.filter(
                status=KnowledgeArticle.Status.PUBLISHED,
                title__icontains=q,
            )[:5]
        return ctx


class TicketUpdateView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketUpdateForm
    template_name = "tickets/form.html"

    def get_queryset(self):
        qs = Ticket.objects.all()
        if not self.request.user.is_technician:
            qs = qs.filter(created_by=self.request.user)
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not request.user.is_technician:
            if ticket.created_by_id != request.user.id or ticket.status != Ticket.Status.NEW:
                messages.error(request, "Nie możesz edytować tego zgłoszenia.")
                return redirect("tickets:detail", pk=ticket.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance._changed_by = self.request.user
        messages.success(self.request, "Zgłoszenie zostało zaktualizowane.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tickets:detail", kwargs={"pk": self.object.pk})


@login_required
@require_POST
def ticket_add_comment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not request.user.is_technician and ticket.created_by_id != request.user.id:
        return HttpResponseForbidden()

    comment_form = CommentForm(request.POST, user=request.user)

    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        comment.save()

        for f in request.FILES.getlist("files"):
            TicketAttachment.objects.create(
                ticket=ticket,
                comment=comment,
                file=f,
                original_name=f.name,
                uploaded_by=request.user,
            )
        messages.success(request, "Komentarz dodany.")

    return redirect("tickets:detail", pk=ticket.pk)


@login_required
def attachment_download(request, pk):
    att = get_object_or_404(TicketAttachment, pk=pk)
    ticket = att.ticket
    if not request.user.is_technician and ticket.created_by_id != request.user.id:
        return HttpResponseForbidden()
    return FileResponse(att.file.open("rb"), as_attachment=True, filename=att.original_name)
