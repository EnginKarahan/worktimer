from django import forms
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile, WorkSchedule, EMPLOYMENT_TYPES, FEDERAL_STATES, ROLE_CHOICES

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
            "employment_type", "weekly_work_hours", "annual_leave_days",
            "hire_date", "federal_state", "manager", "phone", "department",
            "leave_carry_over", "max_carry_over_days",
        ]
        widgets = {
            "hire_date": forms.DateInput(attrs={"type": "date"}),
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
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="Bis",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("Enddatum muss nach Startdatum liegen.")
        return cleaned


class AbsenceRejectForm(forms.Form):
    comment = forms.CharField(
        label="Ablehnungsgrund",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
