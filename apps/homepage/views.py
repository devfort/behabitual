from django.views.generic import ListView, View, TemplateView
from apps.habits.models import Habit
from apps.onboarding.forms import HabitForm

class HomepageView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            homepage_view = UserDashboard.as_view()
        else:
            homepage_view = LoggedOutHomepageView.as_view()
        return homepage_view(request, *args, **kwargs)

class UserDashboard(ListView):
    model = Habit
    template_name = 'homepage/user_dashboard.html'

    def get_queryset(self):
        return self.request.user.habits.all()

    def is_dashboard(self):
        return True

class LoggedOutHomepageView(TemplateView):
    template_name = 'homepage/home.html'
    
    def get_context_data(self, **kwargs):
        ctx = super(LoggedOutHomepageView, self).get_context_data(**kwargs)
        ctx['form'] = HabitForm(prefix="habit")
        return ctx
    