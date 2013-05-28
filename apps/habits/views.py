import json

from django.views.generic import View, DetailView, FormView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _
from django import forms

from apps.habits.models import Habit, habit_archived
from apps.habits.forms import HabitForm
from apps.encouragements import get_encouragement
from lib.metrics import statsd

class HabitDetailView(DetailView):
    model = Habit

    def get_queryset(self):
        return self.request.user.habits.all()


class HabitEditView(UpdateView):
    model = Habit
    form_class = HabitForm
    template_name_suffix = '_edit_form'

    def get_success_url(self):
        return reverse('homepage')


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
        # To make the label for the input dynamic we need to create a new class
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

    def get_context_data(self, **kwargs):
       ctx = super(HabitEncouragementView, self).get_context_data(**kwargs)
       ctx['encouragement'] = get_encouragement(self.get_object())
       return ctx


RECENT_BUCKETS = 20

class HabitPerformanceView(View):

    def get(self, request, *args, **kwargs):
        result = {'habits': []}

        for habit in request.user.habits.filter(archived=False):
            current = habit.get_current_time_period()
            recent_buckets = [None] * RECENT_BUCKETS

            for bucket in habit.get_buckets().filter(index__gt=current.index - RECENT_BUCKETS):
                recent_buckets[bucket.index - current.index - 1] = bucket.value

            result['habits'].append({'description': habit.description,
                                     'resolution': habit.resolution,
                                     'target_value': habit.target_value,
                                     'recent_buckets': recent_buckets})

        return HttpResponse(json.dumps(result), content_type='application/json')
