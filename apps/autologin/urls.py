from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<uidb36>[-0-9a-z]+);(?P<token>[-0-9a-z]+)/', "apps.autologin.views.auto_login"),
)