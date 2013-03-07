from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login
from django.views.generic import TemplateView

import accounts.views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='homepage/home.html'), name='homepage'),
    url(r'^login/$', login, {'template_name': 'accounts/login.html'}, name='login'),
    url(r'^logout/$', accounts.views.LogoutView.as_view(), name='logout'),
    url(r'^password-change/$', 'django.contrib.auth.views.password_change', name='password_change'),
    url(r'^password-change/done/$', 'django.contrib.auth.views.password_change_done', name='password_change_done'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
