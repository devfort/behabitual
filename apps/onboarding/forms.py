from django import forms
from apps.habits.models import RESOLUTION_CHOICES

class HabitForm(forms.Form):
    description = forms.CharField(max_length=100)
    target_value = forms.IntegerField()
    resolution = forms.ChoiceField(
        choices=RESOLUTION_CHOICES,
    )


class ReminderForm(forms.Form):
    pass


class SummaryForm(forms.Form):
    pass
