from datetime import timedelta
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils.timezone import now, localtime

from apps.core.models import AuditLog
from .models import TravelExpenseReport, TravelDay, TravelReceipt

VMA_FULL_DAY = Decimal("28.00")
VMA_PARTIAL_DAY = Decimal("14.00")
BREAKFAST_DEDUCTION = Decimal("5.60")
LUNCH_DEDUCTION = Decimal("11.20")
DINNER_DEDUCTION = Decimal("11.20")
OVERNIGHT_FLAT = Decimal("20.00")
KM_RATE = Decimal("0.30")


class VMACalculatorService:
    def calculate(self, departure, return_dt, day_provisions):
        """
        Returns a list of dicts (one per calendar day) with VMA amounts.
        day_provisions: {date: {"breakfast": bool, "lunch": bool, "dinner": bool}}
        departure/return_dt must be timezone-aware datetimes.
        """
        total_seconds = (return_dt - departure).total_seconds()
        total_minutes = total_seconds / 60

        if total_minutes < 480:
            return []

        dep_date = localtime(departure).date()
        ret_date = localtime(return_dt).date()

        days = []
        if dep_date == ret_date:
            days.append({"date": dep_date, "day_type": "SINGLE", "vma_base": VMA_PARTIAL_DAY})
        else:
            days.append({"date": dep_date, "day_type": "DEPARTURE", "vma_base": VMA_PARTIAL_DAY})
            current = dep_date + timedelta(days=1)
            while current < ret_date:
                days.append({"date": current, "day_type": "FULL", "vma_base": VMA_FULL_DAY})
                current += timedelta(days=1)
            days.append({"date": ret_date, "day_type": "RETURN", "vma_base": VMA_PARTIAL_DAY})

        result = []
        for entry in days:
            d = entry["date"]
            prov = day_provisions.get(d, {})
            deduction = Decimal("0")
            if prov.get("breakfast"):
                deduction += BREAKFAST_DEDUCTION
            if prov.get("lunch"):
                deduction += LUNCH_DEDUCTION
            if prov.get("dinner"):
                deduction += DINNER_DEDUCTION
            vma_net = max(Decimal("0"), entry["vma_base"] - deduction)
            result.append({
                "date": d,
                "day_type": entry["day_type"],
                "vma_base": entry["vma_base"],
                "vma_deduction": deduction,
                "vma_net": vma_net,
            })
        return result

    def calculate_transport(self, transport_type, km):
        if transport_type == "PRIVATE_CAR":
            return (km * KM_RATE).quantize(Decimal("0.01"))
        return Decimal("0")


class TravelExpenseService:
    def create_report(self, user, cleaned_data, request=None):
        with transaction.atomic():
            report = TravelExpenseReport.objects.create(
                user=user,
                title=cleaned_data["title"],
                destination=cleaned_data["destination"],
                departure_datetime=cleaned_data["departure_datetime"],
                return_datetime=cleaned_data["return_datetime"],
                is_domestic=cleaned_data.get("is_domestic", True),
                transport_type=cleaned_data.get("transport_type", "PRIVATE_CAR"),
                private_car_km=cleaned_data.get("private_car_km") or Decimal("0"),
                booking_class=cleaned_data.get("booking_class", ""),
                discount_card=cleaned_data.get("discount_card", ""),
                notes=cleaned_data.get("notes", ""),
            )
            self._rebuild_days(report, {})
            self._recalculate_totals(report)
            AuditLog.log(
                actor=request.user if request else user,
                action="travel_report_created",
                entity=report,
                new={"status": "DRAFT", "title": report.title},
                request=request,
            )
        return report

    def update_report(self, report, cleaned_data, day_provisions=None, request=None):
        with transaction.atomic():
            report.title = cleaned_data["title"]
            report.destination = cleaned_data["destination"]
            report.departure_datetime = cleaned_data["departure_datetime"]
            report.return_datetime = cleaned_data["return_datetime"]
            report.is_domestic = cleaned_data.get("is_domestic", True)
            report.transport_type = cleaned_data.get("transport_type", "PRIVATE_CAR")
            report.private_car_km = cleaned_data.get("private_car_km") or Decimal("0")
            report.booking_class = cleaned_data.get("booking_class", "")
            report.discount_card = cleaned_data.get("discount_card", "")
            report.notes = cleaned_data.get("notes", "")
            report.save()
            self._rebuild_days(report, day_provisions or {})
            self._recalculate_totals(report)
            AuditLog.log(
                actor=request.user if request else report.user,
                action="travel_report_updated",
                entity=report,
                new={"title": report.title, "destination": report.destination},
                request=request,
            )
        return report

    def update_day_provisions(self, report, day_provisions, request=None):
        """Update meal/overnight flags for existing TravelDay rows and recalculate VMA."""
        with transaction.atomic():
            calc = VMACalculatorService()
            vma_data = calc.calculate(
                report.departure_datetime,
                report.return_datetime,
                day_provisions,
            )
            vma_map = {entry["date"]: entry for entry in vma_data}
            for day in report.days.all():
                prov = day_provisions.get(day.date, {})
                day.breakfast_provided = prov.get("breakfast", False)
                day.lunch_provided = prov.get("lunch", False)
                day.dinner_provided = prov.get("dinner", False)
                day.overnight = prov.get("overnight", False)
                day.overnight_flat_rate = prov.get("overnight_flat_rate", False)
                if day.date in vma_map:
                    entry = vma_map[day.date]
                    day.vma_base = entry["vma_base"]
                    day.vma_deduction = entry["vma_deduction"]
                    day.vma_net = entry["vma_net"]
                day.save()
            self._recalculate_totals(report)

    def _rebuild_days(self, report, day_provisions):
        calc = VMACalculatorService()
        if report.is_domestic:
            vma_data = calc.calculate(
                report.departure_datetime,
                report.return_datetime,
                day_provisions,
            )
        else:
            # Auslandssätze noch nicht implementiert; VMA = 0
            vma_data = []

        existing = {d.date: d for d in report.days.all()}
        report.days.all().delete()

        for entry in vma_data:
            old = existing.get(entry["date"])
            TravelDay.objects.create(
                report=report,
                date=entry["date"],
                day_type=entry["day_type"],
                vma_base=entry["vma_base"],
                vma_deduction=entry["vma_deduction"],
                vma_net=entry["vma_net"],
                breakfast_provided=old.breakfast_provided if old else False,
                lunch_provided=old.lunch_provided if old else False,
                dinner_provided=old.dinner_provided if old else False,
                overnight=old.overnight if old else False,
                overnight_flat_rate=old.overnight_flat_rate if old else False,
            )

    def _recalculate_totals(self, report):
        calc = VMACalculatorService()
        vma = report.days.aggregate(t=Sum("vma_net"))["t"] or Decimal("0")
        transport = calc.calculate_transport(report.transport_type, report.private_car_km)
        agg = report.receipts.aggregate(
            total=Sum("gross_amount"),
            employer=Sum("gross_amount", filter=models.Q(paid_by_employer=True)),
        )
        receipts = agg["total"] or Decimal("0")
        employer_paid = agg["employer"] or Decimal("0")
        report.vma_total = vma
        report.transport_total = transport
        report.receipts_total = receipts
        report.employer_paid_total = employer_paid
        report.grand_total = vma + transport + receipts
        report.to_reimburse_total = vma + transport + (receipts - employer_paid)
        report.save(
            update_fields=[
                "vma_total", "transport_total", "receipts_total",
                "employer_paid_total", "grand_total", "to_reimburse_total", "updated_at",
            ]
        )

    def add_receipt(self, report, cleaned_data, file=None, request=None):
        with transaction.atomic():
            receipt = TravelReceipt.objects.create(
                report=report,
                date=cleaned_data["date"],
                gross_amount=cleaned_data["gross_amount"],
                currency=cleaned_data.get("currency", "EUR"),
                original_amount=cleaned_data.get("original_amount"),
                exchange_rate=cleaned_data.get("exchange_rate"),
                vat_rate=cleaned_data.get("vat_rate", "19"),
                category=cleaned_data["category"],
                description=cleaned_data.get("description", ""),
                taxi_reason=cleaned_data.get("taxi_reason", ""),
                paid_by_employer=cleaned_data.get("paid_by_employer", False),
                file=file,
            )
            self._recalculate_totals(report)
            AuditLog.log(
                actor=request.user if request else report.user,
                action="travel_receipt_added",
                entity=report,
                new={"receipt_id": receipt.pk, "amount": str(receipt.gross_amount)},
                request=request,
            )
        return receipt

    def delete_receipt(self, receipt, request=None):
        report = receipt.report
        with transaction.atomic():
            if receipt.file:
                receipt.file.delete(save=False)
            AuditLog.log(
                actor=request.user if request else report.user,
                action="travel_receipt_deleted",
                entity=report,
                old={"receipt_id": receipt.pk, "amount": str(receipt.gross_amount)},
                request=request,
            )
            receipt.delete()
            self._recalculate_totals(report)

    def submit_report(self, report, request=None):
        with transaction.atomic():
            report = TravelExpenseReport.objects.select_for_update().get(pk=report.pk)
            if report.status != "DRAFT":
                raise ValueError("Nur Entwürfe können eingereicht werden.")
            report.status = "SUBMITTED"
            report.submitted_at = now()
            report.save(update_fields=["status", "submitted_at", "updated_at"])
            AuditLog.log(
                actor=request.user if request else report.user,
                action="travel_report_submitted",
                entity=report,
                new={"status": "SUBMITTED"},
                request=request,
            )
            from apps.travel.tasks import notify_hr_new_travel_report
            notify_hr_new_travel_report.delay(report.pk)
        return report

    def approve_report(self, report, reviewer, comment="", request=None):
        with transaction.atomic():
            report = TravelExpenseReport.objects.select_for_update().get(pk=report.pk)
            if report.status != "SUBMITTED":
                raise ValueError("Nur eingereichte Berichte können genehmigt werden.")
            report.status = "APPROVED"
            report.reviewer = reviewer
            report.reviewed_at = now()
            report.review_comment = comment
            report.save(
                update_fields=["status", "reviewer", "reviewed_at", "review_comment", "updated_at"]
            )
            AuditLog.log(
                actor=reviewer,
                action="travel_report_approved",
                entity=report,
                new={"status": "APPROVED", "reviewer": reviewer.pk},
                request=request,
            )
            from apps.travel.tasks import notify_employee_travel_decision
            notify_employee_travel_decision.delay(report.pk)
        return report

    def reject_report(self, report, reviewer, comment="", request=None):
        with transaction.atomic():
            report = TravelExpenseReport.objects.select_for_update().get(pk=report.pk)
            if report.status != "SUBMITTED":
                raise ValueError("Nur eingereichte Berichte können abgelehnt werden.")
            report.status = "REJECTED"
            report.reviewer = reviewer
            report.reviewed_at = now()
            report.review_comment = comment
            report.save(
                update_fields=["status", "reviewer", "reviewed_at", "review_comment", "updated_at"]
            )
            AuditLog.log(
                actor=reviewer,
                action="travel_report_rejected",
                entity=report,
                new={"status": "REJECTED", "comment": comment},
                request=request,
            )
            from apps.travel.tasks import notify_employee_travel_decision
            notify_employee_travel_decision.delay(report.pk)
        return report

    def reopen_report(self, report, request=None):
        with transaction.atomic():
            report = TravelExpenseReport.objects.select_for_update().get(pk=report.pk)
            if report.status != "REJECTED":
                raise ValueError("Nur abgelehnte Berichte können wiedereröffnet werden.")
            report.status = "DRAFT"
            report.reviewer = None
            report.reviewed_at = None
            report.review_comment = ""
            report.save(
                update_fields=["status", "reviewer", "reviewed_at", "review_comment", "updated_at"]
            )
            AuditLog.log(
                actor=request.user if request else report.user,
                action="travel_report_reopened",
                entity=report,
                new={"status": "DRAFT"},
                request=request,
            )
        return report


def generate_travel_pdf(report):
    from django.conf import settings
    from weasyprint import HTML

    context = {
        "report": report,
        "days": list(report.days.all()),
        "receipts": list(report.receipts.all()),
        "company_name": getattr(settings, "COMPANY_NAME", "Alhambra"),
        "generated_at": now(),
    }
    html = render_to_string("travel/travel_expense_pdf.html", context)
    return HTML(string=html).write_pdf()
