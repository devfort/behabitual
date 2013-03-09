from django.views.generic import View, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import ugettext as _
from django import forms

from apps.habits.models import Habit, record_habit_archived
from lib.metrics import statsd

class HabitDetailView(DetailView):
    model = Habit

    def get_queryset(self):
        return self.request.user.habits.all()


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
        record_habit_archived.send(obj)
        obj.save()
        return HttpResponseRedirect(self.get_success_url())

class HabitRecordView(FormView):
    model = Habit
    template_name = "habits/habit_record_form.html"

    def get_queryset(self):
        return self.request.user.habits.all()

    # Bit of a hack. Including SingleObjectMixin brings in a get_context_data
    # which is not usable stand-alone
    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs.get('pk'))
        except Habit.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})

    def get_context_data(self, **kwargs):
        kwargs['habit'] = self.get_object()
        return super(HabitRecordView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        habit = self.get_object()
        time_period = habit.get_time_period(form.cleaned_data['date'])
        habit.record(time_period, form.cleaned_data['value'])
        return HttpResponseRedirect(reverse('habit_encouragement', args=[habit.id]))

    def get_form_class(self):
        habit = self.get_object()
        time_period = habit.get_current_time_period()

        class HabitForm(forms.Form):
            date = forms.DateField(
                required=True,
                initial=time_period.date,
                widget=forms.HiddenInput
            )
            value = forms.IntegerField(min_value=0, required=True)
        return HabitForm

class HabitEncouragementView(DetailView):
    model = Habit
    template_name = "habits/habit_encouragement.html"
