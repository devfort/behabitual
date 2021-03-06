from django import forms
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from apps.habits.models import RESOLUTIONS_NO_MONTH

User = get_user_model()

DAYS_OF_WEEK = (
    ('MONDAY', mark_safe('<b>Every</b> Monday')),
    ('TUESDAY', mark_safe('<b>Every</b> Tuesday')),
    ('WEDNESDAY', mark_safe('<b>Every</b> Wednesday')),
    ('THURSDAY', mark_safe('<b>Every</b> Thursday')),
    ('FRIDAY', mark_safe('<b>Every</b> Friday')),
    ('SATURDAY', mark_safe('<b>Every</b> Saturday')),
    ('SUNDAY', mark_safe('<b>Every</b> Sunday')),
)

DAYS = (
    'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY',
    'FRIDAY', 'SATURDAY', 'SUNDAY',
)

HOURS = map(
    lambda hour: (hour, '%02d:00' % hour),
    range(24)
)


class ReminderDaysField(forms.MultipleChoiceField):
    def prepare_value(self, value):
        if isinstance(value, int):
            booleans = [value & (1 << i) != 0 for i in range(7)]
            return map(lambda x: x[0], filter(lambda x: x[1], zip(DAYS, booleans)))
        else:
            return value

    def clean(self, value):
        booleans = map(lambda d: d in value, DAYS)
        day_bits = [1 << i if d else 0 for i, d in enumerate(booleans)]
        return reduce(lambda x, y: x | y, day_bits)


class HabitForm(forms.Form):
    """
    Captures basic Habit information. The first step of the OnboardingWizard.
    """
    description = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': ' brush my teeth'},
    ))
    target_value = forms.IntegerField(
        widget=forms.TextInput(attrs={'placeholder': '2'}),
    )
    resolution = forms.ChoiceField(
        choices=RESOLUTIONS_NO_MONTH,
    )


class ExistingUserReminderForm(forms.Form):
    """
    Captures Habit reminder information. The second step of the
    OnboardingWizard.
    """
    trigger = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'close the dishwasher'}),
    )
    days = ReminderDaysField(
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
        return email


class NewUserReminderForm(ExistingUserReminderForm, EmailUniqueness):
    email = forms.EmailField(required=False)

    def clean_email(self):
        trigger = self.cleaned_data.get('trigger')
        days = self.cleaned_data.get('days')
        email = self.cleaned_data.get('email')
        if (trigger or days) and not email:
            raise forms.ValidationError("Email is required for reminder")
        user_count = User.objects.filter(email=email).count()
        if user_count > 0:
            raise forms.ValidationError("Email is already taken")
        return self.cleaned_data.get('email')


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
