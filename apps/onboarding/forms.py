from django import forms
from django.contrib.auth import get_user_model
from apps.habits.models import RESOLUTION_CHOICES

User = get_user_model()

DAYS_OF_WEEK = (
    ('MONDAY', 'Monday'),
    ('TUESDAY', 'Tuesday'),
    ('WEDNESDAY', 'Wednesday'),
    ('THURSDAY', 'Thursday'),
    ('FRIDAY', 'Friday'),
    ('SATURDAY', 'Saturday'),
    ('SUNDAY', 'Sunday'),
)

HOURS = zip(range(24), range(24))


class HabitForm(forms.Form):
    """
    Captures basic Habit information. The first step of the OnboardingWizard.
    """
    description = forms.CharField(max_length=100)
    target_value = forms.IntegerField()
    resolution = forms.ChoiceField(
        choices=RESOLUTION_CHOICES,
    )


class ExistingUserReminderForm(forms.Form):
    """
    Captures Habit reminder information. The second step of the
    OnboardingWizard.
    """
    trigger = forms.CharField(max_length=50, required=False)
    days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    hour = forms.ChoiceField(choices=HOURS, required=False)


class EmailUniqueness(object):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_count = User.objects.filter(email=email).count()
        if user_count > 0:
            raise forms.ValidationError("Email is already taken")


class NewUserReminderForm(ExistingUserReminderForm, EmailUniqueness):
    email = forms.EmailField(required=False)

    def clean(self):
        cleaned_data = super(ExistingUserReminderForm, self).clean()
        trigger = cleaned_data.get('trigger')
        days = cleaned_data.get('days')
        email = cleaned_data.get('email')

        if (trigger or days) and not email:
            raise forms.ValidationError("Email is required for reminder")
        return cleaned_data


class NewUserSummaryForm(forms.Form, EmailUniqueness):
    """
    Captures user information. The final step of the OnboardingWizard.
    """
    email = forms.EmailField()

class ExistingUserSummaryForm(forms.Form):
    """
    The final step of the AddHabitWizard.
    """
    pass
