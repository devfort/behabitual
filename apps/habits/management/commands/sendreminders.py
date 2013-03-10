from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.habits.models import Habit
from apps.habits.reminders import send_email

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        """
        Send all pending habit reminders. This command should be called on a
        cronjob once an hour (ideally shortly after the top of the hour).
        """
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        for habit in Habit.scheduled_for_reminder(now.weekday(), now.hour):
            # Only send the reminder if either
            #   a) the habit has never had any reminders send for it
            #   b) the habit last had a reminder sent at least an hour ago
            if habit.reminder_last_sent is None or habit.reminder_last_sent < now:
                habit.reminder_last_sent = now
                habit.save()
                send_email(habit)

