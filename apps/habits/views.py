from django.views.generic import View, DetailView, FormView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _
from django import forms

from apps.habits.models import Habit, habit_archived
from apps.habits.forms import HabitForm
from lib.metrics import statsd

class HabitDetailView(DetailView):
    model = Habit

    def get_queryset(self):
        return self.request.user.habits.all()


class HabitEditView(UpdateView):
    model = Habit
    form_class = HabitForm
    success_url = '/'
    #success_url = reverse('homepage')
    template_name_suffix = '_edit_form'


class HabitArchiveView(SingleObjectMixin, View):
    model = Habit

    def get_queryset(self):
        return self.request.user.habits.all()

    def get_success_url(self):
        return self.request.POST.get("next",
            self.request.META.get('HTTP_REFERER', reverse('habit', kwargs={'pk': self.get_object().id}))
        )

    @never_cache
    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.archived = request.POST.get("archive") == "1"
        habit_archived.send(obj)
        obj.save()
        return HttpResponseRedirect(self.get_success_url())

@never_cache
def habit_record_view(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)

    time_periods = habit.get_recent_unentered_time_periods()

    if len(time_periods) == 0:
        return HttpResponseRedirect(reverse('homepage'))

    _forms = []

    for period in time_periods:
        # To make the lable for the input dynamic we need to create a new class
        # each time. This might be better done as a Widget instead...?
        class HabitForm(forms.Form):
            date = forms.DateField(required=True, widget=forms.HiddenInput)
            value = forms.IntegerField(min_value=0, label=period.friendly_date())

        if request.method == 'POST': # If the form has been submitted...
            data = request.POST
            initial = None
        else:
            data = None
            initial = {'date': period.date}

        _forms.append(HabitForm(data=data, initial=initial, prefix=str(period.index)))

    if request.method == 'POST': # If the form has been submitted...
        if all(map(lambda f: f.is_valid(), _forms)):
            # TODO: record all data points
            for form in _forms:
                time_period = habit.get_time_period(form.cleaned_data['date'])
                habit.record(time_period, form.cleaned_data['value'])
            return HttpResponseRedirect(reverse('habit_encouragement', args=[habit.id]))

    return render(request, 'habits/habit_record_form.html', {
        'forms': _forms,
        'habit': habit,
    })


class HabitEncouragementView(DetailView):
    model = Habit
    template_name = "habits/habit_encouragement.html"
