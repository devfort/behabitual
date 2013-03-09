from django.views.generic import ListView, View, TemplateView
from apps.habits.models import Habit

class HomepageView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            homepage_view = UserDashboard.as_view()
        else:
            homepage_view = TemplateView.as_view(
                template_name='homepage/home.html'
            )
        return homepage_view(request, *args, **kwargs)

class UserDashboard(ListView):
    model = Habit
    template_name = 'homepage/user_dashboard.html'

    def get_queryset(self):
        return self.request.user.habits.all()
