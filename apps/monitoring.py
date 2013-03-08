from django.contrib.auth.signals import user_logged_out, user_logged_in
from django.dispatch import receiver

from apps.accounts.views import user_changed_password
from lib.metrics import statsd


@receiver(user_logged_out)
def record_statsd_logged_out(sender, **kwargs):
    statsd.incr('user.logouts')

@receiver(user_logged_in)
def record_statsd_logged_in(sender, **kwargs):
    statsd.incr('user.logins')

@receiver(user_changed_password)
def record_statsd_changed_passsword(sender, **kwargs):
    statsd.incr('user.changed_password')
