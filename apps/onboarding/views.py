from datetime import datetime
from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import update_last_login
from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.contrib.sites.models import get_current_site
from django.db import connection
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, int_to_base36
from django.views.decorators.cache import never_cache

from apps.onboarding.forms import HabitForm, \
    NewUserReminderForm, ExistingUserReminderForm, \
    NewUserSummaryForm, ExistingUserSummaryForm

from apps.accounts.signals import user_created
from apps.autologin.views import FlexibleTokenGenerator
from apps.habits.models import Habit
from apps.habits.signals import habit_created

from util.render_to_email import render_to_email

User = get_user_model()


class OnboardingWizard(NamedUrlSessionWizardView):
    """
    Wizard to add new habits. It will also create a user if the current user
    isn't authenticated.
    """
    template_name = 'onboarding/wizard.html'
    send_habit_email = False

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

    def get_context_data(self, *args, **kwargs):
        data = super(OnboardingWizard, self).get_context_data(*args, **kwargs)
        data['habit'] = self.get_cleaned_data_for_step('habit')
        data['reminder'] = self.get_cleaned_data_for_step('reminder')
        return data

    def save(self):
        """
        Saves the habit.
        """

        habit_form = self.form_list[0]
        reminder_form = self.form_list[1]

        habit = Habit.objects.create(
            user=self.user,
            description=habit_form.cleaned_data.get('description'),
            resolution=habit_form.cleaned_data.get('resolution'),
            target_value=habit_form.cleaned_data.get('target_value'),
            reminder=reminder_form.cleaned_data.get('trigger'),
            reminder_hour=reminder_form.cleaned_data.get('hour') or 0,
            reminder_days=reminder_form.cleaned_data.get('days') or 0,
            start=datetime.now(),
        )
        habit_created.send(habit)

        if self.send_habit_email:
            render_to_email(
                text_template='onboarding/emails/habit_created.txt',
                html_template='onboarding/emails/habit_created.html',
                to=(self.user,),
                subject='You set up a new habit!',
            )

    @property
    def user(self):
        try:
            u = self._user
        except AttributeError:
            u = self._user = self.create_user()
        return u

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

        current_site = get_current_site(self.request)
        site_name = current_site.name
        domain = current_site.domain

        c = {
            'email': user.email,
            'domain': domain,
            'site_name': site_name,
            'uid': int_to_base36(user.pk),
            'user': user,
            'token': token_generator.make_token(user),
            'protocol': self.request.is_secure() and 'https' or 'http',
        }

        render_to_email(
            text_template='onboarding/emails/welcome.txt',
            html_template='onboarding/emails/welcome.html',
            to=(user,),
            subject='Welcome!',
            opt_out=False,
            context=c,
        )

        return user


class AddHabitWizard(OnboardingWizard):
    """
    Add a habit, when you're already authenticated.
    """
    send_habit_email = True

    @property
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


class EmailConfirmationTokenGenerator(FlexibleTokenGenerator):
    key_salt = "apps.onboarding.EmailConfirmationTokenGenerator"

token_generator = EmailConfirmationTokenGenerator()


@never_cache
def confirm_email_address(
    request,
    uidb36,
    token,
    error_template="onboarding/failed_email_confirm.html",
    template="onboarding/email_confirm.html",
    redirect_to="/"
):
    redirect = request.GET.get('next', None)
    args = request.GET.copy()
    if 'next' in args:
        del args['next']
    args = args.urlencode()
    if redirect is None:
        redirect = redirect_to
    if args != "":
        if '?' in redirect:
            redirect += '&'
        else:
            redirect += '?'
        redirect += args

    try:
        user = User.objects.get(pk=base36_to_int(uidb36))
    except (ValueError, User.DoesNotExist):
        user = None

    if request.user.is_authenticated() and request.user != user:
        user = None

    if user is None or not token_generator.check_token(user, token):
        return TemplateResponse(request, error_template, {}, status=400)

    if request.method == 'POST':
        if request.user.is_authenticated():
            if request.user == user:
                user.is_active = True
                user.save()
                update_last_login(None, user)
                return HttpResponseRedirect(redirect)
            else:
                return TemplateResponse(request, error_template, {}, status=400)

        user.is_active = True
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return HttpResponseRedirect(redirect)
    else:
        return TemplateResponse(request, template, { 'next': redirect, 'email': user.email })
