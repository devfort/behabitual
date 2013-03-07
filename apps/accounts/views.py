from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView


class LogoutView(TemplateView):
    """
    Logs the user out.
    """

    template_name = "accounts/logout.html"

    def get_next_url(self):
        next = self.request.POST.get("next", None)
        if next is None:
            next = reverse('homepage')
        return next

    def post(self, request):
        logout(self.request)
        return HttpResponseRedirect(self.get_next_url())
