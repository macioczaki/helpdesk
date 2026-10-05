from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import AssetAssignForm, AssetForm, LicenseForm
from .models import Asset, AssetAssignment, License

from io import BytesIO

import qrcode

class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = "assets/list.html"
    context_object_name = "assets"
    paginate_by = 20

    def get_queryset(self):
        qs = Asset.objects.select_related("category", "location", "assigned_to")
        status = self.request.GET.get("status")
        if status in Asset.Status.values:
            qs = qs.filter(status=status)
        type_ = self.request.GET.get("type")
        if type_ in Asset.Type.values:
            qs = qs.filter(type=type_)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(tag__icontains=q)
                | Q(name__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(model_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Asset.Status.choices
        ctx["types"] = Asset.Type.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_type"] = self.request.GET.get("type", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignments"] = self.object.assignments.select_related("user")[:50]
        ctx["assign_form"] = AssetAssignForm()
        return ctx


class AssetCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = Asset
    form_class = AssetForm
    template_name = "assets/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Zasób został dodany.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("assets:detail", kwargs={"pk": self.object.pk})


class AssetUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = Asset
    form_class = AssetForm
    template_name = "assets/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Zasób zaktualizowany.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("assets:detail", kwargs={"pk": self.object.pk})


@require_POST
def asset_assign(request, pk):
    if not request.user.is_authenticated or not request.user.is_technician:
        return redirect("assets:detail", pk=pk)
    asset = get_object_or_404(Asset, pk=pk)
    form = AssetAssignForm(request.POST)
    if form.is_valid():
        new_user = form.cleaned_data["user"]
        now = timezone.now().date()

        # zamknij poprzednie aktywne przypisanie
        asset.assignments.filter(to_date__isnull=True).update(to_date=now)

        if new_user:
            AssetAssignment.objects.create(
                asset=asset,
                user=new_user,
                from_date=now,
                comment=form.cleaned_data.get("comment", ""),
            )
            asset.assigned_to = new_user
            asset.status = Asset.Status.IN_USE
        else:
            asset.assigned_to = None
            asset.status = Asset.Status.IN_STOCK
        asset.save()

        messages.success(request, "Przypisanie zaktualizowane.")
    else:
        messages.error(request, "Nie udało się zapisać przypisania.")
    return redirect("assets:detail", pk=pk)


class LicenseListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = License
    template_name = "assets/license_list.html"
    context_object_name = "licenses"


class LicenseCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = License
    form_class = LicenseForm
    template_name = "assets/license_form.html"

    def get_success_url(self):
        return reverse_lazy("assets:license_list")


class LicenseUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = License
    form_class = LicenseForm
    template_name = "assets/license_form.html"

    def get_success_url(self):
        return reverse_lazy("assets:license_list")

@login_required
def asset_qr(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    img = qrcode.make(asset.tag)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")

@login_required
def scan(request):
    """Strona skanowania — pole tekstowe + przekierowanie."""
    tag = request.GET.get("tag", "").strip()
    if tag:
        return redirect("assets:scan_resolve", tag=tag)
    return render(request, "assets/scan.html", {"tag": tag})


@login_required
def scan_resolve(request, tag):
    asset = Asset.objects.filter(tag__iexact=tag).first()
    if not asset:
        messages.error(request, f"Nie znaleziono zasobu o tagu: {tag}")
        return render(request, "assets/scan.html", {"tag": tag})
    return redirect("assets:detail", pk=asset.pk)


@login_required
def labels_print(request):
    """Generuje PDF z etykietami QR dla wybranych zasobów."""
    ids = request.GET.getlist("ids")
    if not ids and request.GET.get("all"):
        qs = Asset.objects.filter(status__in=[Asset.Status.IN_USE, Asset.Status.IN_STOCK])
    else:
        qs = Asset.objects.filter(pk__in=ids)

    assets = list(qs[:500])
    if not assets:
        messages.warning(request, "Nie wybrano żadnych zasobów.")
        return redirect("assets:list")

    from .labels import build_labels_pdf
    pdf = build_labels_pdf(assets, base_url=request.build_absolute_uri("/"))
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="etykiety.pdf"'
    return response

@login_required
def csv_template_view(request):
    from .services import csv_template
    response = HttpResponse(csv_template(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="szablon_majatek.csv"'
    return response


@login_required
def import_view(request):
    if not request.user.is_technician:
        return HttpResponseForbidden()
    result = None
    if request.method == "POST" and request.FILES.get("file"):
        from .services import import_assets_from_csv
        result = import_assets_from_csv(request.FILES["file"], request.user)
    return render(request, "assets/import.html", {"result": result})


@login_required
def export_view(request):
    from .services import export_assets_to_xlsx
    qs = Asset.objects.all()
    status = request.GET.get("status")
    if status in Asset.Status.values:
        qs = qs.filter(status=status)
    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(tag__icontains=q) | Q(name__icontains=q) | Q(serial_number__icontains=q)
        )
    data = export_assets_to_xlsx(qs)
    response = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="majatek.xlsx"'
    return response

class AlertsView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    template_name = "assets/alerts.html"
    context_object_name = "alerts"

    def get_queryset(self):
        return Asset.objects.none()

    def get_context_data(self, **kwargs):
        from .alerts import collect_alerts
        ctx = super().get_context_data(**kwargs)
        ctx["data"] = collect_alerts()
        return ctx