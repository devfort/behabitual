from django.contrib.auth.signals import user_logged_out, user_logged_in
from django.dispatch import receiver

from apps.accounts.signals import user_changed_password
from apps.habits.signals import (habit_archived,
                                 habit_created,
                                 habit_data_recorded)
from lib.metrics import statsd


@receiver(user_logged_out)
def record_user_logged_out(sender, **kwargs):
    statsd.incr('user.logouts')

@receiver(user_logged_in)
def record_user_logged_in(sender, **kwargs):
    statsd.incr('user.logins')

@receiver(user_changed_password)
def record_user_changed_password(sender, **kwargs):
    statsd.incr('user.changed_password')

@receiver(habit_data_recorded)
def record_habit_data_recorded(sender, **kwargs):
    statsd.incr('habit.recorded')

@receiver(habit_archived)
def record_habit_archived(sender, **kwargs):
    if sender.archived:
        counter = 'habit.archived'
    else:
        counter = 'habit.unarchived'
    statsd.incr(counter)

@receiver(habit_created)
def record_habit_created(sender, **kwargs):
    statsd.incr('habit.created')
