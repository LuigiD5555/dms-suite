"""Generic report endpoint built from ``reports.config``.

This is intentionally separate from the legacy report views.  It lets a public
fork add report templates by editing configuration instead of editing Python
view classes for every customer-specific document.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.apps import apps
from django.http import Http404, HttpResponse
from django.views import View

from .config import get_report_template
from .report_tools import convert_to_pdf, replace_variables_in_docx


def resolve_attr(obj: Any, dotted_path: str, default: str = "") -> str:
    """Resolve dotted attributes and zero-arg methods safely.

    Example: ``curp.get_nombre_completo`` calls ``obj.curp.get_nombre_completo()``
    when the final attribute is callable.
    """

    current = obj
    for part in dotted_path.split("."):
        current = getattr(current, part, None)
        if current is None:
            return default
    if callable(current):
        current = current()
    return str(current) if current is not None else default


class GenerateConfiguredReportView(View):
    """Generate a report using a declarative config entry.

    Expected POST fields:
    - ``report_type``: key from ``REPORT_TEMPLATES``
    - object id field configured by ``request_field``; for example ``personnel_id``
    """

    def post(self, request, *args, **kwargs):
        report_type = request.POST.get("report_type")
        if not report_type:
            raise Http404("Missing report_type")

        try:
            config = get_report_template(report_type)
        except ValueError as exc:
            raise Http404(str(exc)) from exc

        model = apps.get_model(config["model"])
        request_field = config.get("request_field", "object_id")
        lookup_value = request.POST.get(request_field)
        if not lookup_value:
            raise Http404(f"Missing {request_field}")

        lookup_field = config.get("lookup_field", "id")
        try:
            instance = model.objects.get(**{lookup_field: lookup_value})
        except model.DoesNotExist as exc:
            raise Http404(f"Object not found for {lookup_field}={lookup_value}") from exc

        data = {
            placeholder: resolve_attr(instance, attr_path)
            for placeholder, attr_path in config.get("variables", {}).items()
        }

        template_path = config["template_path"]
        output_dir = Path(config.get("output_dir", "media/reports"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_format = config.get("output_format", "pdf").lower()

        temporary_docx = replace_variables_in_docx(template_path, data)
        output_path = output_dir / f"{report_type}_{lookup_value}.{output_format}"

        if output_format == "pdf":
            generated_path = convert_to_pdf(temporary_docx, str(output_path))
        else:
            generated_path = temporary_docx

        if not generated_path or not Path(generated_path).exists():
            raise Http404("Report generation failed")

        content_type = "application/pdf" if output_format == "pdf" else "application/octet-stream"
        with open(generated_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{Path(generated_path).name}"'
        return response
