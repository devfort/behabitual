import datetime

from django.test import TestCase

from apps.accounts.models import User
from apps.encouragements.models import Generator, \
    most_periods_succeeding_in_a_row
from apps.habits.models import Bucket, Habit


class MockUser(object):
    def __init__(self, id=1):
        self.pk = id


class EncouragementsTest(TestCase):
    def setUp(self):
        self.user = MockUser(4)
        self.providers = (
            lambda user: None,
            lambda user: 'a',
            lambda user: 'b',
        )

    def test_returns_none_with_no_providers(self):
        generator = Generator([])
        self.assertIsNone(generator(self.user))

    def test_returns_the_encouragement_from_a_single_provider(self):
        encouragement = object()
        provider = lambda user: encouragement
        generator = Generator([provider])
        self.assertEqual(encouragement, generator(self.user))

    def test_returns_none_if_the_provider_returns_none(self):
        provider = lambda user: None
        generator = Generator([provider])
        self.assertIsNone(generator(self.user))

    def test_returns_user_derived_encouragements_from_a_provider(self):
        provider = lambda user: user.pk
        generator = Generator([provider])
        self.assertEqual(4, generator(self.user))

    def test_returns_an_encouragement_from_a_set_of_providers(self):
        generator = Generator(self.providers)
        results = [generator(self.user) for i in range(100)]
        self.assertEqual(set(('a', 'b')), set(results))


class MostPeriodsSucceedingInARow(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')

    def test_one_succeeding(self):
        today = datetime.date(2013, 1, 1)
        h = Habit.objects.create(
            start=today,
            user=self.user,
            resolution='day',
        )
        h.record(h.get_time_period(today), 1)
        periods = most_periods_succeeding_in_a_row(h)
        self.assertIsNotNone(periods)

    def test_thingy(self):
        today = datetime.date(2013, 1, 1)
        h = Habit.objects.create(
            start=today,
            user=self.user,
            resolution='day',
        )
        h.record(h.get_time_period(today), 1)
        periods = most_periods_succeeding_in_a_row(h)
        self.assertIsNotNone(periods)

    def test_no(self):
        self.fail()

    def test_empty(self):
        today = datetime.date.today()
        h = Habit(start=today, user=self.user, resolution='day')
        self.assertIsNone(most_periods_succeeding_in_a_row(h))
