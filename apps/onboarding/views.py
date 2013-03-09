from datetime import datetime
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from django.contrib.formtools.wizard.views import SessionWizardView

from forms import HabitForm, ReminderForm, SummaryForm
from apps.habits.models import Habit

User = get_user_model()


class OnboardingWizard(SessionWizardView):
    """
    Wizard to add new habits. It will also create a user if the current user
    isn't authenticated.
    """
    template_name = 'onboarding/wizard.html'

    def done(self, form_list, **kwargs):
        self.form_list = form_list
        self.save()
        return HttpResponseRedirect('/')

    def get_form_initial(self, step):
        if step == '2':
            reminder_data = self.get_cleaned_data_for_step('1')
            return {'email': reminder_data.get('email')}
        else:
            return super(OnboardingWizard, self).get_form_initial(step)

    def save(self):
        """
        Saves the habit.
        """
        habit_form = self.form_list[0]
        habit = Habit.objects.create(
            user=self.user(),
            description=habit_form.cleaned_data.get('description'),
            resolution=habit_form.cleaned_data.get('resolution'),
            target_value=habit_form.cleaned_data.get('target_value'),
            start=datetime.now(),
        )
        #TODO Create a reminder

    def user(self):
        return self.create_user()

    def create_user(self):
        """
        Creates and logs in a new user for the habit, or just returns the
        current user if they're already authenticated.
        """
        summary_form = self.form_list[2]
        user = User.objects.create_user(
            email=summary_form.cleaned_data.get('email'),
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, user)
        return user


class AddHabitWizard(OnboardingWizard):
    def user(self):
        return self.request.user


onboarding_wizard = OnboardingWizard.as_view([HabitForm, ReminderForm, SummaryForm])
