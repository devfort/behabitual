from django.views.generic import View, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from apps.habits.models import Habit

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
        obj.save()
        return HttpResponseRedirect(self.get_success_url())
