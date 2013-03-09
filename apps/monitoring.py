from django.contrib.auth.signals import user_logged_out, user_logged_in
from django.dispatch import receiver

from apps.accounts.views import user_changed_password
from apps.habits.models import record_habit_data, record_habit_archived
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

@receiver(record_habit_data)
def record_habit_data_entry(sender, **kwargs):
    statsd.incr('habit.recorded')

@receiver(record_habit_archived)
def record_habit_archived(sender, **kwargs):
    if sender.archived:
        counter = 'habit.archived'
    else:
        counter = 'habit.unarchived'
    statsd.incr(counter)
