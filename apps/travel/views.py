from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.permissions import hr_required

from .forms import TravelDayProvisionFormSet, TravelExpenseReportForm, TravelReceiptForm, TravelRejectForm
from .models import TravelExpenseReport, TravelReceipt
from .services import TravelExpenseService, generate_travel_pdf


# ─── Employee views ────────────────────────────────────────────────────────────

@login_required
def travel_list(request):
    reports = TravelExpenseReport.objects.filter(user=request.user).select_related("user")
    return render(request, "travel/list.html", {"reports": reports})


@login_required
def travel_create(request):
    if request.method == "POST":
        form = TravelExpenseReportForm(request.POST)
        if form.is_valid():
            report = TravelExpenseService().create_report(
                request.user, form.cleaned_data, request=request
            )
            messages.success(request, "Reisekostenabrechnung erstellt. Bitte füllen Sie die Details aus.")
            return redirect("travel:edit", pk=report.pk)
    else:
        form = TravelExpenseReportForm()
    return render(request, "travel/create.html", {"form": form})


@login_required
def travel_edit(request, pk):
    report = get_object_or_404(TravelExpenseReport, pk=pk, user=request.user)
    if not report.is_editable:
        messages.info(request, "Diese Abrechnung kann nicht mehr bearbeitet werden.")
        return redirect("travel:detail", pk=pk)

    if request.method == "POST":
        action = request.POST.get("action", "save")

        if action == "save_report":
            form = TravelExpenseReportForm(request.POST, instance=report)
            if form.is_valid():
                TravelExpenseService().update_report(
                    report, form.cleaned_data, request=request
                )
                messages.success(request, "Reisedaten gespeichert.")
                return redirect("travel:edit", pk=pk)
            day_formset = TravelDayProvisionFormSet(
                queryset=report.days.all(), prefix="days"
            )

        elif action == "save_provisions":
            day_formset = TravelDayProvisionFormSet(
                request.POST, queryset=report.days.all(), prefix="days"
            )
            if day_formset.is_valid():
                provisions = {}
                for day_form in day_formset:
                    day_obj = day_form.instance
                    provisions[day_obj.date] = {
                        "breakfast": day_form.cleaned_data.get("breakfast_provided", False),
                        "lunch": day_form.cleaned_data.get("lunch_provided", False),
                        "dinner": day_form.cleaned_data.get("dinner_provided", False),
                        "overnight": day_form.cleaned_data.get("overnight", False),
                        "overnight_flat_rate": day_form.cleaned_data.get("overnight_flat_rate", False),
                    }
                TravelExpenseService().update_day_provisions(report, provisions, request=request)
                messages.success(request, "Verpflegungsangaben gespeichert.")
                return redirect("travel:edit", pk=pk)
            form = TravelExpenseReportForm(instance=report)

        else:
            form = TravelExpenseReportForm(instance=report)
            day_formset = TravelDayProvisionFormSet(
                queryset=report.days.all(), prefix="days"
            )
    else:
        form = TravelExpenseReportForm(instance=report)
        day_formset = TravelDayProvisionFormSet(
            queryset=report.days.all(), prefix="days"
        )

    receipt_form = TravelReceiptForm()
    return render(request, "travel/edit.html", {
        "report": report,
        "form": form,
        "day_formset": day_formset,
        "receipt_form": receipt_form,
    })


@login_required
def travel_detail(request, pk):
    report = get_object_or_404(TravelExpenseReport, pk=pk, user=request.user)
    return render(request, "travel/detail.html", {"report": report})


@login_required
def travel_submit(request, pk):
    if request.method != "POST":
        return redirect("travel:detail", pk=pk)
    report = get_object_or_404(TravelExpenseReport, pk=pk, user=request.user)
    if report.status != "DRAFT":
        messages.error(request, "Dieser Bericht kann nicht eingereicht werden.")
        return redirect("travel:detail", pk=pk)
    TravelExpenseService().submit_report(report, request=request)
    messages.success(request, "Abrechnung erfolgreich eingereicht.")
    return redirect("travel:detail", pk=pk)


@login_required
def travel_reopen(request, pk):
    if request.method != "POST":
        return redirect("travel:detail", pk=pk)
    report = get_object_or_404(TravelExpenseReport, pk=pk, user=request.user)
    if report.status != "REJECTED":
        messages.error(request, "Dieser Bericht kann nicht wiedereröffnet werden.")
        return redirect("travel:detail", pk=pk)
    TravelExpenseService().reopen_report(report, request=request)
    messages.success(request, "Abrechnung wurde zur Bearbeitung wiedereröffnet.")
    return redirect("travel:edit", pk=pk)


@login_required
def travel_pdf(request, pk):
    report = get_object_or_404(
        TravelExpenseReport, pk=pk, user=request.user, status__in=["SUBMITTED", "APPROVED"]
    )
    pdf = generate_travel_pdf(report)
    filename = f"reisekosten_{report.pk}_{report.departure_datetime.date()}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def travel_receipt_add(request, pk):
    report = get_object_or_404(TravelExpenseReport, pk=pk, user=request.user)
    if not report.is_editable:
        messages.error(request, "Diese Abrechnung kann nicht mehr bearbeitet werden.")
        return redirect("travel:detail", pk=pk)
    if request.method == "POST":
        form = TravelReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            TravelExpenseService().add_receipt(
                report,
                form.cleaned_data,
                file=form.cleaned_data.get("file"),
                request=request,
            )
            messages.success(request, "Beleg hinzugefügt.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("travel:edit", pk=pk)


@login_required
def travel_receipt_delete(request, pk, receipt_pk):
    if request.method != "POST":
        return redirect("travel:edit", pk=pk)
    report = get_object_or_404(TravelExpenseReport, pk=pk, user=request.user)
    receipt = get_object_or_404(TravelReceipt, pk=receipt_pk, report=report)
    if not report.is_editable:
        messages.error(request, "Diese Abrechnung kann nicht mehr bearbeitet werden.")
        return redirect("travel:detail", pk=pk)
    TravelExpenseService().delete_receipt(receipt, request=request)
    messages.success(request, "Beleg gelöscht.")
    return redirect("travel:edit", pk=pk)


# ─── HR views ──────────────────────────────────────────────────────────────────

@hr_required
def hr_travel_list(request):
    status_filter = request.GET.get("status", "")
    reports = TravelExpenseReport.objects.select_related("user").order_by("-submitted_at", "-created_at")
    if status_filter:
        reports = reports.filter(status=status_filter)
    from .models import REPORT_STATUS_CHOICES
    return render(request, "travel/hr_list.html", {
        "reports": reports,
        "status_filter": status_filter,
        "status_choices": REPORT_STATUS_CHOICES,
    })


@hr_required
def hr_travel_detail(request, pk):
    report = get_object_or_404(TravelExpenseReport, pk=pk)
    reject_form = TravelRejectForm()
    return render(request, "travel/hr_detail.html", {
        "report": report,
        "reject_form": reject_form,
    })


@hr_required
def hr_travel_approve(request, pk):
    if request.method != "POST":
        return redirect("travel:hr_detail", pk=pk)
    report = get_object_or_404(TravelExpenseReport, pk=pk, status="SUBMITTED")
    comment = request.POST.get("comment", "")
    TravelExpenseService().approve_report(report, request.user, comment=comment, request=request)
    messages.success(request, "Abrechnung genehmigt.")
    return redirect("travel:hr_detail", pk=pk)


@hr_required
def hr_travel_reject(request, pk):
    if request.method != "POST":
        return redirect("travel:hr_detail", pk=pk)
    report = get_object_or_404(TravelExpenseReport, pk=pk, status="SUBMITTED")
    form = TravelRejectForm(request.POST)
    if form.is_valid():
        TravelExpenseService().reject_report(
            report, request.user, comment=form.cleaned_data["comment"], request=request
        )
        messages.success(request, "Abrechnung abgelehnt.")
    else:
        messages.error(request, "Bitte geben Sie einen Ablehnungsgrund an.")
    return redirect("travel:hr_detail", pk=pk)


@hr_required
def hr_travel_pdf(request, pk):
    report = get_object_or_404(TravelExpenseReport, pk=pk)
    pdf = generate_travel_pdf(report)
    filename = f"reisekosten_{report.pk}_{report.departure_datetime.date()}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
