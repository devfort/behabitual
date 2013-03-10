from django.core.management.base import BaseCommand, CommandError

from apps.habits.models import Habit
from apps.habits.reminders import send_data_collection_email

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        """
        Send all pending habit data collection emails. This command should be
        called on a cronjob once a day (probably at the start of the working
        day).
        """
        for habit in Habit.objects.filter(send_data_collection_emails=True):
            send_data_collection_email(habit)

