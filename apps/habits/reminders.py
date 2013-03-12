import datetime

from django.utils.translation import ugettext_lazy as _

from util.render_to_email import render_to_email

def send_reminder_email(habit):
    return render_to_email(
        text_template='emails/habits/reminder.txt',
        html_template='emails/habits/reminder.html',
        to=(habit.user,),
        subject=habit.description,
        context=dict(description=habit.description),
    )

def send_data_collection_email(habit, today=None):
    if today is None:
        today = datetime.date.today()

    if not habit.send_data_collection_emails:
        return

    if today == habit.start:
        # Don't ask for data from before the habit was created
        return

    if habit.resolution == 'weekday':
        # Don't ask for data on Sundays and Mondays
        if today.weekday() in [6, 0]:
            return

    if habit.resolution == 'weekendday':
        # Don't ask for data from Tuesday to Saturday
        if today.weekday() in range(1, 6):
            return

    if habit.resolution == 'week':
        # Don't ask for data unless today is a Monday
        if today.weekday() != 0:
            return

    if habit.resolution == 'month':
        # Don't ask for data unless today is the 1st of a new month
        if today.day != 1:
            return

    time_period_name = {
        'day':        _('yesterday'),
        'weekday':    _('yesterday'),
        'weekendday': _('yesterday'),
        'week':       _('last week'),
        'month':      _('last month'),
    }[habit.resolution]

    context = {'time_period_name': time_period_name}

    return render_to_email(
        text_template='emails/habits/data_collection.txt',
        html_template='emails/habits/data_collection.html',
        to=(habit.user,),
        subject='Let us know how you did',
        context=context,
    )

