import datetime

from django.core import mail
from django.test import TestCase

from apps.accounts.models import User
from apps.habits.models import Habit
from apps.habits.reminders import send_reminder_email, send_data_collection_email
from lib import test_helpers as helpers

DATA_COLLECTION_FIXTURES = (
    # habit resolution, send date, should send?
    ('day', '2013-03-04', False), # shouldn't send if only just created
    ('day', '2013-03-05', True),
    ('day', '2013-03-06', True),
    ('day', '2013-03-07', True),
    ('weekday', '2013-03-08', True),
    ('weekday', '2013-03-09', True),
    ('weekday', '2013-03-10', False),
    ('weekday', '2013-03-11', False),
    ('weekday', '2013-03-12', True),
    ('weekendday', '2013-03-09', False),
    ('weekendday', '2013-03-10', True),
    ('weekendday', '2013-03-11', True),
    ('weekendday', '2013-03-12', False),
    ('week', '2013-03-10', False),
    ('week', '2013-03-11', True),
    ('week', '2013-03-12', False),
    ('month', '2013-03-13', False),
    ('month', '2013-03-31', False),
    ('month', '2013-04-01', True),
    ('month', '2013-04-02', False),
)

class TestReminders(TestCase):

    def setUp(self):
        self.u = User.objects.create(email='foo@bar.com', password='SecretZ!')
        self.h = Habit.objects.create(user=self.u,
                                      description='Frobble your wingdangle',
                                      start=datetime.date(2013, 3, 4))

    def test_send_reminder_email(self):
        send_reminder_email(self.h)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Frobble your wingdangle' in mail.outbox[0].subject)

    def test_disable_send_data_collection_email(self):
        self.h.send_data_collection_emails = False

        result = send_data_collection_email(self.h)

        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 0)


def test_send_data_collection_email(self, fixture):
    resolution, today, should_send = fixture
    today_date = helpers.parse_isodate(today)

    self.h.resolution = resolution
    result = send_data_collection_email(self.h, today=today_date)

    if should_send:
        self.assertIsNotNone(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Let us know' in mail.outbox[0].subject)
    else:
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 0)

helpers.attach_fixture_tests(TestReminders, test_send_data_collection_email, DATA_COLLECTION_FIXTURES)
