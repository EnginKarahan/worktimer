import os
from decimal import Decimal

from django import forms
from django.conf import settings

from .models import TravelExpenseReport, TravelDay, TravelReceipt, BOOKING_CLASS_CHOICES, DISCOUNT_CARD_CHOICES

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/tiff",
}


class TravelExpenseReportForm(forms.ModelForm):
    class Meta:
        model = TravelExpenseReport
        fields = [
            "title",
            "destination",
            "departure_datetime",
            "return_datetime",
            "is_domestic",
            "transport_type",
            "private_car_km",
            "booking_class",
            "discount_card",
            "notes",
        ]
        widgets = {
            "departure_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "return_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["private_car_km"].required = False
        self.fields["booking_class"].required = False
        self.fields["discount_card"].required = False
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.Select)):
                field.widget.attrs.setdefault("class", "w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500")

    def clean(self):
        cleaned = super().clean()
        dep = cleaned.get("departure_datetime")
        ret = cleaned.get("return_datetime")
        if dep and ret and ret < dep:
            raise forms.ValidationError("Rückkehr muss nach der Abfahrt liegen.")
        transport = cleaned.get("transport_type")
        km = cleaned.get("private_car_km") or Decimal("0")
        if transport == "PRIVATE_CAR" and km <= 0:
            self.add_error("private_car_km", "Bitte gefahrene km angeben.")
        return cleaned


class TravelDayProvisionForm(forms.ModelForm):
    class Meta:
        model = TravelDay
        fields = [
            "breakfast_provided",
            "lunch_provided",
            "dinner_provided",
            "overnight",
            "overnight_flat_rate",
        ]
        labels = {
            "breakfast_provided": "Frühstück gestellt",
            "lunch_provided": "Mittagessen gestellt",
            "dinner_provided": "Abendessen gestellt",
            "overnight": "Übernachtung",
            "overnight_flat_rate": "Pauschale (20 €)",
        }

    def clean(self):
        cleaned = super().clean()
        overnight = cleaned.get("overnight")
        flat = cleaned.get("overnight_flat_rate")
        if flat and not overnight:
            cleaned["overnight"] = True
        return cleaned


TravelDayProvisionFormSet = forms.modelformset_factory(
    TravelDay,
    form=TravelDayProvisionForm,
    extra=0,
    can_delete=False,
)


class TravelReceiptForm(forms.ModelForm):
    class Meta:
        model = TravelReceipt
        fields = [
            "date",
            "gross_amount",
            "currency",
            "original_amount",
            "exchange_rate",
            "vat_rate",
            "category",
            "description",
            "taxi_reason",
            "paid_by_employer",
            "file",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "file": forms.FileInput(
                attrs={
                    "accept": ".pdf,.jpg,.jpeg,.png,.gif,.webp,.tif,.tiff",
                }
            ),
            "description": forms.Textarea(attrs={"rows": 2}),
            "taxi_reason": forms.Textarea(attrs={"rows": 2, "placeholder": "z. B. Zugverspätung – Termin nicht rechtzeitig per ÖPNV erreichbar"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["original_amount"].required = False
        self.fields["exchange_rate"].required = False
        self.fields["description"].required = False
        self.fields["taxi_reason"].required = False
        self.fields["file"].required = False
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.setdefault("class", "w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("category") == "TAXI" and not cleaned.get("taxi_reason", "").strip():
            self.add_error("taxi_reason", "Bei Taxi-Fahrten ist eine Begründung erforderlich.")
        return cleaned

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            return f

        max_bytes = getattr(settings, "TRAVEL_RECEIPT_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
        if f.size > max_bytes:
            raise forms.ValidationError(
                f"Datei zu groß. Maximal {max_bytes // (1024 * 1024)} MB erlaubt."
            )

        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Nur PDF und Bilder (JPEG, PNG, GIF, WebP, TIFF) sind erlaubt."
            )

        # PDF magic byte check
        if ext == ".pdf":
            header = f.read(4)
            f.seek(0)
            if header != b"%PDF":
                raise forms.ValidationError("Die Datei ist keine gültige PDF-Datei.")

        # Image integrity check via Pillow
        if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}:
            try:
                from PIL import Image
                img = Image.open(f)
                img.verify()
            except Exception:
                raise forms.ValidationError("Die Bilddatei ist beschädigt oder ungültig.")
            f.seek(0)

        return f


class TravelRejectForm(forms.Form):
    comment = forms.CharField(
        label="Ablehnungsgrund",
        widget=forms.Textarea(attrs={"rows": 3, "class": "w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"}),
        required=True,
    )
