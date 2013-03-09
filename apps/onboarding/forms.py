from django import forms
from apps.habits.models import RESOLUTION_CHOICES

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


class ReminderForm(forms.Form):
    """
    Captures Habit reminder information. The second step of the
    OnboardingWizard.
    """
    email = forms.EmailField(required=False)
    trigger = forms.CharField(max_length=50, required=False)
    days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    hour = forms.ChoiceField(choices=HOURS, required=False)


class SummaryForm(forms.Form):
    """
    Captures user information. The final set of the OnboardingWizard.
    """
    email = forms.EmailField()
