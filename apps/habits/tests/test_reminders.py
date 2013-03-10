import datetime

from django.core import mail
from django.test import TestCase

from apps.accounts.models import User
from apps.habits.models import Habit
from apps.habits.reminders import send_email

class TestReminders(TestCase):

    def test_send_email(self):
        u = User.objects.create(email='foo@bar.com', password='SecretZ!')
        h = Habit.objects.create(user=u,
                                 description='Frobble your wingdangle',
                                 start=datetime.date.today())

        send_email(h)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Frobble your wingdangle' in mail.outbox[0].subject)
