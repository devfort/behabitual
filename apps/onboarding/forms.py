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
    description = forms.CharField(max_length=100)
    target_value = forms.IntegerField()
    resolution = forms.ChoiceField(
        choices=RESOLUTION_CHOICES,
    )


class ReminderForm(forms.Form):
    email = forms.EmailField()
    trigger = forms.CharField(max_length=50)
    days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
    )
    hour = forms.ChoiceField(choices=HOURS)


class SummaryForm(forms.Form):
    email = forms.EmailField()
