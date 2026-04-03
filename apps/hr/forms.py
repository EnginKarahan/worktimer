from django import forms
from django.contrib.auth import get_user_model
from apps.accounts.models import (
    UserProfile,
    WorkSchedule,
    EMPLOYMENT_TYPES,
    FEDERAL_STATES,
    ROLE_CHOICES,
)
from apps.projects.models import Project

User = get_user_model()


class EmployeeUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]
        labels = {
            "first_name": "Vorname",
            "last_name": "Nachname",
            "email": "E-Mail",
            "is_active": "Aktiv",
        }


class EmployeeProfileForm(forms.ModelForm):
    roles = forms.MultipleChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Rollen",
    )

    class Meta:
        model = UserProfile
        fields = [
            "employment_type",
            "weekly_work_hours",
            "annual_leave_days",
            "hire_date",
            "federal_state",
            "manager",
            "phone",
            "department",
            "leave_carry_over",
            "max_carry_over_days",
        ]
        labels = {
            "employment_type": "Beschäftigungsart",
            "weekly_work_hours": "Wochenstunden",
            "annual_leave_days": "Urlaubstage pro Jahr",
            "hire_date": "Einstellungsdatum",
            "federal_state": "Bundesland",
            "manager": "Vorgesetzte/r",
            "leave_carry_over": "Urlaubsübertrag erlaubt",
            "max_carry_over_days": "Max. Übertragstage",
        }
        widgets = {
            "hire_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current = list(self.instance.user.roles.values_list("role", flat=True))
            self.fields["roles"].initial = current

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            from apps.accounts.models import UserRole

            chosen = set(self.cleaned_data.get("roles", []))
            UserRole.objects.filter(user=profile.user).delete()
            for r in chosen:
                UserRole.objects.create(user=profile.user, role=r)
        return profile


class SickLeaveForm(forms.Form):
    start_date = forms.DateField(
        label="Von",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    end_date = forms.DateField(
        label="Bis",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    au_vorhanden = forms.BooleanField(
        label="AU-Bescheinigung liegt vor",
        required=False,
    )
    au_eingereicht_am = forms.DateField(
        label="AU eingereicht am",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    notes = forms.CharField(
        label="Hinweis (intern)",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("Enddatum muss nach Startdatum liegen.")
        return cleaned


class AbsenceTypeChangeForm(forms.Form):
    from apps.absences.models import LeaveType
    leave_type = forms.ModelChoiceField(
        queryset=None,
        label="Neuer Abwesenheitstyp",
    )
    reason = forms.CharField(
        label="Begründung der Änderung",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.absences.models import LeaveType
        self.fields["leave_type"].queryset = LeaveType.objects.all()


class AbsenceRejectForm(forms.Form):
    comment = forms.CharField(
        label="Ablehnungsgrund",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )


class WorkScheduleForm(forms.ModelForm):
    class Meta:
        model = WorkSchedule
        fields = [
            "monday_minutes",
            "tuesday_minutes",
            "wednesday_minutes",
            "thursday_minutes",
            "friday_minutes",
            "saturday_minutes",
            "sunday_minutes",
            "effective_from",
            "effective_to",
        ]
        labels = {
            "effective_from": "Gültig ab",
            "effective_to": "Gültig bis (optional)",
        }
        widgets = {
            "effective_from": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "effective_to": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        day_labels = {
            "monday_minutes": "Montag",
            "tuesday_minutes": "Dienstag",
            "wednesday_minutes": "Mittwoch",
            "thursday_minutes": "Donnerstag",
            "friday_minutes": "Freitag",
            "saturday_minutes": "Samstag",
            "sunday_minutes": "Sonntag",
        }
        for field in day_labels:
            if field in self.fields:
                self.fields[field].label = day_labels[field]
                self.fields[field].help_text = "Minuten"

    def clean(self):
        cleaned = super().clean()
        from_date = cleaned.get("effective_from")
        to_date = cleaned.get("effective_to")
        if from_date and to_date and to_date < from_date:
            raise forms.ValidationError("Enddatum muss nach Startdatum liegen.")
        return cleaned

    @property
    def weekly_hours(self):
        # Use cleaned_data after validation, fall back to instance values
        if hasattr(self, "cleaned_data") and self.cleaned_data:
            total = sum([
                (self.cleaned_data.get("monday_minutes", 0) or 0),
                (self.cleaned_data.get("tuesday_minutes", 0) or 0),
                (self.cleaned_data.get("wednesday_minutes", 0) or 0),
                (self.cleaned_data.get("thursday_minutes", 0) or 0),
                (self.cleaned_data.get("friday_minutes", 0) or 0),
            ])
        elif self.instance and self.instance.pk:
            total = (
                (self.instance.monday_minutes or 0) +
                (self.instance.tuesday_minutes or 0) +
                (self.instance.wednesday_minutes or 0) +
                (self.instance.thursday_minutes or 0) +
                (self.instance.friday_minutes or 0)
            )
        else:
            return 40.0
        return round(total / 60, 2)


class TimeEntryCreateForm(forms.Form):
    date = forms.DateField(
        label="Datum",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    start_time = forms.TimeField(
        label="Startzeit",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    end_time = forms.TimeField(
        label="Endzeit",
        widget=forms.TimeInput(attrs={"type": "time"}),
        required=False,
    )
    break_minutes = forms.IntegerField(
        label="Pause (Minuten)",
        initial=0,
        min_value=0,
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label="Projekt",
        empty_label="-- Kein Projekt --",
    )
    notes = forms.CharField(
        label="Notizen",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("Endzeit muss nach der Startzeit liegen.")
        return cleaned


class VacationAdjustmentForm(forms.Form):
    days = forms.DecimalField(
        label="Tage",
        decimal_places=1,
        help_text="Positiv = hinzufügen, Negativ = abziehen",
    )
    reason = forms.CharField(
        label="Begründung",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=True,
    )


class OvertimeAdjustmentForm(forms.Form):
    minutes = forms.IntegerField(
        label="Minuten",
        help_text="Positiv = hinzufügen, Negativ = abziehen",
    )
    reason = forms.CharField(
        label="Begründung",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=True,
    )


class TimeEntryDeleteForm(forms.Form):
    reason = forms.CharField(
        label="Löschungsgrund",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=True,
    )
