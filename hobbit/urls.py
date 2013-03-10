from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

import apps.accounts.views
import apps.onboarding.views
import apps.homepage.views
import apps.habits.views

from django.contrib import admin
admin.autodiscover()

def secured_url(path, view, *args, **kwargs):
    return url(path, login_required(view), *args, **kwargs)

urlpatterns = patterns('',
    # url(r'^$', TemplateView.as_view(template_name='homepage/home.html'), name='homepage'),
    url(r'^$', apps.homepage.views.HomepageView.as_view(), name='homepage'),
    url(r'^logout/$', apps.accounts.views.LogoutView.as_view(), name='logout'),
    url(r'^password-change/$', apps.accounts.views.password_change, name='password_change'),
    url(r'^password-change/done/$', 'django.contrib.auth.views.password_change_done', name='password_change_done'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'apps.accounts.views.password_reset_confirm',
        {'post_reset_redirect': '/'},
        name='password_reset_confirm'),
    url(r'^_;', include('apps.autologin.urls')),

    url(r'^add-habit/(?P<step>.+)/$', apps.onboarding.views.add_habit_wizard, name='add_habit_step'),
    url(r'^add-habit/$', apps.onboarding.views.add_habit_wizard, name='add_habit'),

    secured_url(r'^habit/(?P<pk>\d+)/$', apps.habits.views.HabitDetailView.as_view(), name='habit'),
    secured_url(r'^habit/(?P<pk>\d+)/archive$', apps.habits.views.HabitArchiveView.as_view(), name='habit_archive'),
    secured_url(r'^habit/(?P<pk>\d+)/record/$', apps.habits.views.habit_record_view, name='habit_record'),
    secured_url(r'^habit/(?P<pk>\d+)/recorded/$', apps.habits.views.HabitEncouragementView.as_view(), name='habit_encouragement'),

) + patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', {'template_name': 'accounts/login.html'}, name='login'),
    url(r'^accounts/forgot/$', 'password_reset', name='account-forgotten'),
    url(r'^accounts/forgot/done/$', 'password_reset_done'),

    url(r'^styletile$', TemplateView.as_view(template_name='styles/tile.html'), name='styletile'),
)

from apps.monitoring import *
