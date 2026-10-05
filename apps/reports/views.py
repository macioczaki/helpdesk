from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .exporters import export_report_to_xlsx
from .services import build_report, default_range


def _parse_date(value, default):
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return default


class ReportView(RoleRequiredMixin, View):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    template_name = "reports/report.html"

    def get(self, request):
        default_from, default_to = default_range()
        date_from = _parse_date(request.GET.get("from"), default_from)
        date_to = _parse_date(request.GET.get("to"), default_to)
        report = build_report(date_from, date_to)
        return render(request, self.template_name, {"report": report})


class ReportExportView(RoleRequiredMixin, View):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)

    def get(self, request):
        default_from, default_to = default_range()
        date_from = _parse_date(request.GET.get("from"), default_from)
        date_to = _parse_date(request.GET.get("to"), default_to)
        report = build_report(date_from, date_to)
        buf = export_report_to_xlsx(report)
        filename = f"raport_{date_from}_{date_to}.xlsx"
        response = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response