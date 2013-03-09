from collections import namedtuple
import datetime

from django.test import TestCase

from apps.accounts.models import User
from apps.encouragements.models import Generator, \
    most_periods_succeeding_in_a_row
from apps.habits.models import Bucket, Habit

from lib import test_helpers as helpers


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


MPSF = namedtuple('MostPeriodSucceedingFixture', 'start resolution data expects_none')

MOST_PERIOD_SUCCEEDING_FIXTURES = (
    MPSF(start='2013-03-01',
       resolution='day',
       data=(),
       expects_none=True,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 1),),
       expects_none=False,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(
        ('2013-03-01', 1),
        ('2013-03-02', 0),
        ('2013-03-03', 1),
        ('2013-03-04', 1),
        ),
       expects_none=False,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(
        ('2013-03-01', 1),
        ('2013-03-03', 1),
        ('2013-03-04', 1),
        ),
       expects_none=False,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(
        ('2013-03-01', 1),
        ('2013-03-02', 1),
        ('2013-03-04', 1),
        ('2013-03-05', 1),
        ),
       expects_none=True,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(
        ('2013-03-01', 1),
        ('2013-03-03', 1),
        ('2013-03-04', 0),
        ('2013-03-05', 1),
        ('2013-03-06', 1),
        ),
       expects_none=True,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(
        ('2013-03-01', 1),
        ('2013-03-02', 1),
        ('2013-03-03', 0),
        ('2013-03-04', 1),
        ('2013-03-06', 1),
        ),
       expects_none=False,
    ),
    MPSF(start='2013-03-01',
       resolution='day',
       data=(
        ('2013-03-01', 1),
        ('2013-03-02', 1),
        ('2013-03-03', 0),
        ('2013-03-04', 1),
        ('2013-03-05', 1),
        ),
       expects_none=False,
    ),
)


class MostPeriodsSucceedingInARow(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')


def test_most_succeeding_period(self, fixture):
    start, resolution, data, expects_none = fixture
    start_date = helpers.parse_isodate(start)

    h = Habit.objects.create(start=start_date, user=self.user, resolution=resolution)

    for time_period, value in data:
        when = helpers.parse_isodate(time_period)
        h.record(h.get_time_period(when), value)

    periods = most_periods_succeeding_in_a_row(h)
    if expects_none:
        self.assertIsNone(periods)
    else:
        self.assertIsNotNone(periods)

helpers.attach_fixture_tests(MostPeriodsSucceedingInARow, test_most_succeeding_period, MOST_PERIOD_SUCCEEDING_FIXTURES)
