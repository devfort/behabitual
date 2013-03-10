from django import forms
from apps.habits.models import Habit 

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ('archived', 'description', 'target_value', 'resolution')
        widgets = {
            'description': forms.TextInput(),
        }


class HabitEmailOptionsForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ('send_data_collection_emails',)
