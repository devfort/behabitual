from collections import namedtuple
import datetime

from django.test import TestCase

from apps.accounts.models import User
from apps.encouragements.models import (Generator,
                                        longest_streak_succeeding, longest_streak_nonzero,
                                        best_day_ever, best_week_ever, best_month_ever)
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


SF = namedtuple('StreakFixture', 'func start resolution data expects_none')

STREAK_FIXTURES = (
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(),
       expects_none=True),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3),),
       expects_none=False),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3), ('2013-03-02', 1), ('2013-03-03', 3), ('2013-03-04', 3)),
       expects_none=False),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3), ('2013-03-03', 3), ('2013-03-04', 3)),
       expects_none=False),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3), ('2013-03-02', 3), ('2013-03-04', 3), ('2013-03-05', 3)),
       expects_none=True),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 4),
             ('2013-03-03', 3),
             ('2013-03-04', 0),
             ('2013-03-05', 3),
             ('2013-03-06', 7)),
       expects_none=False),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3),
             ('2013-03-02', 3),
             ('2013-03-03', 0),
             ('2013-03-04', 5),
             ('2013-03-06', 3)),
       expects_none=True),
    SF(func=longest_streak_succeeding,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3),
             ('2013-03-02', 3),
             ('2013-03-03', 2),
             ('2013-03-04', 3),
             ('2013-03-05', 3)),
       expects_none=True),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(),
       expects_none=True),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 2),),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 5), ('2013-03-02', 0), ('2013-03-03', 2), ('2013-03-04', 3)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3), ('2013-03-03', 1), ('2013-03-04', 8)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 2), ('2013-03-02', 3), ('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=True),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 1),
             ('2013-03-03', 3),
             ('2013-03-04', 0),
             ('2013-03-05', 1),
             ('2013-03-06', 7)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 3),
             ('2013-03-02', 3),
             ('2013-03-03', 0),
             ('2013-03-04', 1),
             ('2013-03-06', 3)),
       expects_none=True),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='day',
       data=(('2013-03-01', 2),
             ('2013-03-02', 3),
             ('2013-03-03', 0),
             ('2013-03-04', 1),
             ('2013-03-05', 3)),
       expects_none=True),
    # week
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(),
       expects_none=True),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 2),),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 5), ('2013-03-02', 0), ('2013-03-03', 2), ('2013-03-04', 3)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 3), ('2013-03-03', 1), ('2013-03-04', 8)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 2), ('2013-03-02', 3), ('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 1),
             ('2013-03-05', 0),
             ('2013-03-13', 3),
             ('2013-03-20', 1),
             ('2013-03-26', 7)),
       expects_none=False),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 3),
             ('2013-03-05', 3),
             ('2013-03-13', 0),
             ('2013-03-20', 1),
             ('2013-04-03', 3)),
       expects_none=True),
    SF(func=longest_streak_nonzero,
       start='2013-03-01',
       resolution='week',
       data=(('2013-03-01', 2),
             ('2013-03-08', 3),
             ('2013-03-15', 0),
             ('2013-03-22', 1),
             ('2013-03-29', 3)),
       expects_none=True),
)


class TestLongestStreak(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')


def test_longest_streak(self, fixture):
    start_date = helpers.parse_isodate(fixture.start)

    h = Habit.objects.create(start=start_date,
                             user=self.user,
                             resolution=fixture.resolution,
                             target_value=3)

    for time_period, value in fixture.data:
        when = helpers.parse_isodate(time_period)
        h.record(h.get_time_period(when), value)

    periods = fixture.func(h)
    if fixture.expects_none:
        self.assertIsNone(periods)
    else:
        self.assertIsNotNone(periods)

helpers.attach_fixture_tests(TestLongestStreak, test_longest_streak, STREAK_FIXTURES)

BF = namedtuple('BestEverFixture', 'func habit data expects_none')

BEST_EVER_FIXTURES = (
    BF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 0),),
       expects_none=True),
    # Not your "best day ever" if it's your first ever day
    BF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1),),
       expects_none=True),
    BF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 0)),
       expects_none=True),
    BF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 1)),
       expects_none=True),
    BF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 2)),
       expects_none=False),
    BF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 0), ('2013-03-06', 2)),
       expects_none=False),
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 0),),
       expects_none=True),
    # Not your "best week ever" if it's your first ever week...
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1),),
       expects_none=True),
    # ...even if you enter data twice
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=True),
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 0)),
       expects_none=True),
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 1)),
       expects_none=True),
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 2)),
       expects_none=False),
    BF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 0), ('2013-03-12', 2)),
       expects_none=False),
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 0),),
       expects_none=True),
    # Not your "best month ever" if it's your first ever month...
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1),),
       expects_none=True),
    # ...even if you enter data twice
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=True),
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 0)),
       expects_none=True),
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 1)),
       expects_none=True),
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 2)),
       expects_none=False),
    BF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 0), ('2013-04-02', 2)),
       expects_none=False),
)


class TestBestBucketEver(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')


def test_best_ever(self, fixture):
    start, resolution = fixture.habit
    start_date = helpers.parse_isodate(start)

    h = Habit.objects.create(start=start_date, user=self.user, resolution=resolution)

    for time_period, value in fixture.data:
        when = helpers.parse_isodate(time_period)
        h.record(h.get_time_period(when), value)

    res = fixture.func(h)
    if fixture.expects_none:
        self.assertIsNone(res)
    else:
        self.assertIsNotNone(res)

helpers.attach_fixture_tests(TestBestBucketEver, test_best_ever, BEST_EVER_FIXTURES)
