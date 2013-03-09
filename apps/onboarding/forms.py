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


class NewUserReminderForm(ExistingUserReminderForm):
    email = forms.EmailField(required=False)


class NewUserSummaryForm(forms.Form):
    """
    Captures user information. The final step of the OnboardingWizard.
    """
    email = forms.EmailField()


class ExistingUserSummaryForm(forms.Form):
    """
    The final step of the AddHabitWizard.
    """
    pass
