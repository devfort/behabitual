from datetime import datetime
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model, login
from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.db import connection
from django.db.utils import IntegrityError
from django.http import HttpResponse

from apps.accounts.signals import user_created
from apps.habits.models import Habit
from apps.habits.signals import habit_created
from forms import HabitForm, \
    NewUserReminderForm, ExistingUserReminderForm, \
    NewUserSummaryForm, ExistingUserSummaryForm
from util.render_to_email import render_to_email

User = get_user_model()


class OnboardingWizard(NamedUrlSessionWizardView):
    """
    Wizard to add new habits. It will also create a user if the current user
    isn't authenticated.
    """
    template_name = 'onboarding/wizard.html'

    def get_template_names(self):
        return ['onboarding/wizard_%s.html' % self.steps.current]

    def done(self, form_list, **kwargs):
        self.form_list = form_list
        try:
            self.save()
            return HttpResponseRedirect('/')
        except IntegrityError:
            connection.close()
            return HttpResponse('WRONG', content_type='text/html', status=403)

    def get_form_initial(self, step):
        if step == 'summary':
            reminder_data = self.get_cleaned_data_for_step('reminder')
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
        habit_created.send(habit)
        #TODO Create a reminder

    def user(self):
        return self.create_user()

    def create_user(self):
        """
        Creates and logs in a new user for the habit
        """
        summary_form = self.form_list[2]
        user = User.objects.create_user(
            email=summary_form.cleaned_data.get('email'),
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, user)

        user_created.send(user)

        render_to_email(
            text_template='onboarding/emails/welcome.txt',
            html_template='onboarding/emails/welcome.html',
            to=(user,),
            subject='Welcome!',
        )

        return user


class AddHabitWizard(OnboardingWizard):
    """
    Add a habit, when you're already authenticated.
    """
    def user(self):
        return self.request.user


def add_habit_wizard(request, *args, **kwargs):
    """
    Delegates to either the ``OnboardingWizard`` for a logged out user or
    ``AddHabitWizard`` for a logged in user.
    """
    if request.user.is_authenticated():
        wizard = AddHabitWizard.as_view((
            ('habit', HabitForm),
            ('reminder', ExistingUserReminderForm),
            ('summary', ExistingUserSummaryForm),
        ), url_name='add_habit_step', done_step_name='done')
    else:
        wizard = OnboardingWizard.as_view((
            ('habit', HabitForm),
            ('reminder', NewUserReminderForm),
            ('summary', NewUserSummaryForm),
        ), url_name='add_habit_step', done_step_name='done')
    return wizard(request, *args, **kwargs)
