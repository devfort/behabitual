from django import forms
from apps.habits.models import Habit 
from apps.onboarding.forms import DAYS_OF_WEEK, HOURS, ReminderDaysField


class HabitForm(forms.ModelForm):
    reminder_days = ReminderDaysField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
    )
    reminder_hour = forms.ChoiceField(choices=HOURS)

    class Meta:
        model = Habit
        fields = ('archived', 'description', 'target_value', 'resolution',
                  'reminder', 'reminder_days', 'reminder_hour')
        widgets = {
            'description': forms.TextInput(),
            'reminder': forms.TextInput(),
        }


class HabitEmailOptionsForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ('send_data_collection_emails',)
