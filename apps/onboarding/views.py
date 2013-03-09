from django.http import HttpResponseRedirect
from django.contrib.formtools.wizard.views import SessionWizardView
from forms import HabitForm, ReminderForm, SummaryForm

class OnboardingWizard(SessionWizardView):
    template_name = 'onboarding/wizard.html'

    def done(self, form_list, **kwargs):
        return HttpResponseRedirect('/')

onboarding_wizard = OnboardingWizard.as_view([HabitForm, ReminderForm, SummaryForm])
