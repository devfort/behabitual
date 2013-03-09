from collections import namedtuple
import datetime

from django.test import TestCase

from apps.accounts.models import User
from apps.encouragements.models import (ProviderRegistry,
                                        longest_streak_nonzero, longest_streak_succeeding,
                                        best_day_ever, best_week_ever, best_month_ever,
                                        better_than_before,
                                        every_day_this_month_nonzero, every_day_this_month_succeeding,
                                        every_xday_this_month_nonzero, every_xday_this_month_succeeding)
from apps.habits.models import Bucket, Habit

from lib import test_helpers as helpers


class MockHabit(object):
    def __init__(self, pk=1):
        self.pk = pk


class TestProviderRegistry(TestCase):
    def setUp(self):
        self.habit = MockHabit(4)

    def test_returns_none_with_no_providers(self):
        registry = ProviderRegistry()
        self.assertIsNone(registry.get_encouragement(self.habit))

    def test_returns_the_encouragement_from_a_single_provider(self):
        encouragement = object()
        provider = lambda habit: encouragement
        registry = ProviderRegistry()
        registry.register(provider)
        self.assertEqual(encouragement, registry.get_encouragement(self.habit))

    def test_returns_none_if_the_provider_returns_none(self):
        provider = lambda habit: None
        registry = ProviderRegistry()
        registry.register(provider)
        self.assertIsNone(registry.get_encouragement(self.habit))

    def test_returns_habit_derived_encouragements_from_a_provider(self):
        provider = lambda habit: habit.pk
        registry = ProviderRegistry()
        registry.register(provider)
        self.assertEqual(4, registry.get_encouragement(self.habit))

    def test_returns_an_encouragement_from_a_set_of_providers(self):
        registry = ProviderRegistry()
        providers = (
            lambda habit: None,
            lambda habit: 'a',
            lambda habit: 'b',
        )
        for p in providers:
            registry.register(p)
        results = [registry.get_encouragement(self.habit) for i in range(100)]
        self.assertEqual(set(('a', 'b')), set(results))


class TestProviders(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')

# Helper function used by each test_* function below. They call this, and
# might in fact do nothing else, but they give their name to the test methods.
def _test_provider(self, fixture):
    start, resolution = fixture.habit
    start_date = helpers.parse_isodate(start)

    hab = Habit.objects.create(start=start_date,
                               user=self.user,
                               resolution=resolution,
                               target_value=3)

    for time_period, value in fixture.data:
        when = helpers.parse_isodate(time_period)
        hab.record(hab.get_time_period(when), value)

    periods = fixture.func(hab)
    if fixture.expects_none:
        self.assertIsNone(periods)
    else:
        self.assertIsNotNone(periods)

PF = namedtuple('ProviderFixture', 'func habit data expects_none')

STREAK_FIXTURES = (
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(),
       expects_none=True),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3),),
       expects_none=False),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3), ('2013-03-02', 1), ('2013-03-03', 3), ('2013-03-04', 3)),
       expects_none=False),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3), ('2013-03-03', 3), ('2013-03-04', 3)),
       expects_none=False),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3), ('2013-03-02', 3), ('2013-03-04', 3), ('2013-03-05', 3)),
       expects_none=True),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 4),
             ('2013-03-03', 3),
             ('2013-03-04', 0),
             ('2013-03-05', 3),
             ('2013-03-06', 7)),
       expects_none=False),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3),
             ('2013-03-02', 3),
             ('2013-03-03', 0),
             ('2013-03-04', 5),
             ('2013-03-06', 3)),
       expects_none=True),
    PF(func=longest_streak_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3),
             ('2013-03-02', 3),
             ('2013-03-03', 2),
             ('2013-03-04', 3),
             ('2013-03-05', 3)),
       expects_none=True),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(),
       expects_none=True),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 2),),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 5), ('2013-03-02', 0), ('2013-03-03', 2), ('2013-03-04', 3)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3), ('2013-03-03', 1), ('2013-03-04', 8)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 2), ('2013-03-02', 3), ('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=True),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 1),
             ('2013-03-03', 3),
             ('2013-03-04', 0),
             ('2013-03-05', 1),
             ('2013-03-06', 7)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 3),
             ('2013-03-02', 3),
             ('2013-03-03', 0),
             ('2013-03-04', 1),
             ('2013-03-06', 3)),
       expects_none=True),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-01', 2),
             ('2013-03-02', 3),
             ('2013-03-03', 0),
             ('2013-03-04', 1),
             ('2013-03-05', 3)),
       expects_none=True),
    # week
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(),
       expects_none=True),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 2),),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 5), ('2013-03-02', 0), ('2013-03-03', 2), ('2013-03-04', 3)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 3), ('2013-03-03', 1), ('2013-03-04', 8)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 2), ('2013-03-02', 3), ('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 1),
             ('2013-03-05', 0),
             ('2013-03-13', 3),
             ('2013-03-20', 1),
             ('2013-03-26', 7)),
       expects_none=False),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 3),
             ('2013-03-05', 3),
             ('2013-03-13', 0),
             ('2013-03-20', 1),
             ('2013-04-03', 3)),
       expects_none=True),
    PF(func=longest_streak_nonzero,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 2),
             ('2013-03-08', 3),
             ('2013-03-15', 0),
             ('2013-03-22', 1),
             ('2013-03-29', 3)),
       expects_none=True),
)


def test_longest_streak(self, fixture):
    _test_provider(self, fixture)
helpers.attach_fixture_tests(TestProviders, test_longest_streak, STREAK_FIXTURES)


BEST_EVER_FIXTURES = (
    PF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 0),),
       expects_none=True),
    # Not your "best day ever" if it's your first ever day
    PF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1),),
       expects_none=True),
    PF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 0)),
       expects_none=True),
    PF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 1)),
       expects_none=True),
    PF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 2)),
       expects_none=False),
    PF(func=best_day_ever,
       habit=('2013-03-04', 'day'),
       data=(('2013-03-04', 1), ('2013-03-05', 0), ('2013-03-06', 2)),
       expects_none=False),
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 0),),
       expects_none=True),
    # Not your "best week ever" if it's your first ever week...
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1),),
       expects_none=True),
    # ...even if you enter data twice
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=True),
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 0)),
       expects_none=True),
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 1)),
       expects_none=True),
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 2)),
       expects_none=False),
    PF(func=best_week_ever,
       habit=('2013-03-04', 'week'),
       data=(('2013-03-04', 1), ('2013-03-11', 0), ('2013-03-12', 2)),
       expects_none=False),
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 0),),
       expects_none=True),
    # Not your "best month ever" if it's your first ever month...
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1),),
       expects_none=True),
    # ...even if you enter data twice
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-03-05', 3)),
       expects_none=True),
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 0)),
       expects_none=True),
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 1)),
       expects_none=True),
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 2)),
       expects_none=False),
    PF(func=best_month_ever,
       habit=('2013-03-04', 'month'),
       data=(('2013-03-04', 1), ('2013-04-01', 0), ('2013-04-02', 2)),
       expects_none=False),
)


def test_best_ever(self, fixture):
    _test_provider(self, fixture)
helpers.attach_fixture_tests(TestProviders, test_best_ever, BEST_EVER_FIXTURES)


BETTERER_FIXTURES = (
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(),
       expects_none=True),
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-08', 3),),
       expects_none=True),
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 3),('2013-03-06', 5),),
       expects_none=False),
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 5),('2013-03-06', 5),),
       expects_none=True),
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 5),('2013-03-06', 3),),
       expects_none=True),
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 3),('2013-03-15', 5),),
       expects_none=True),
    PF(func=better_than_before,
       habit=('2013-03-01', 'week'),
       data=(('2013-03-01', 3),('2013-03-7', 0),('2013-03-15', 5),),
       expects_none=False),
)


def test_better_than_before(self, fixture):
    _test_provider(self, fixture)
helpers.attach_fixture_tests(TestProviders, test_better_than_before, BETTERER_FIXTURES)


EVERY_DAY_ALL              = [['2013-03-%02d' % (n + 1), 1] for n in range(31)]
EVERY_DAY_MISSING_ONE      = [['2013-03-%02d' % (n + 1), 1] for n in range(31) if n != 10]
EVERY_DAY_ONE_ZERO         = [['2013-03-%02d' % (n + 1), 0 if n == 10 else 1] for n in range(31)]
EVERY_DAY_DAY_AFTER        = EVERY_DAY_ALL[:] + [('2013-04-01', 1)]
EVERY_DAY_S_ALL            = [['2013-03-%02d' % (n + 1), 3] for n in range(31)]
EVERY_DAY_S_MISSING_ONE    = [['2013-03-%02d' % (n + 1), 4] for n in range(31) if n != 10]
EVERY_DAY_S_ONE_ZERO       = [['2013-03-%02d' % (n + 1), 2 if n == 10 else 3] for n in range(31)]
EVERY_DAY_S_DAY_AFTER      = EVERY_DAY_ALL[:] + [('2013-04-01', 4)]
EVERY_MONDAY               = [['2013-03-%02d' % (n + 1), 1] for n in range(31) if n % 7 == 3]
EVERY_TUESDAY              = [['2013-03-%02d' % (n + 1), 1] for n in range(31) if n % 7 == 4]
EVERY_SUNDAY               = [['2013-03-%02d' % (n + 1), 1] for n in range(31) if n % 7 == 2]
EVERY_SUNDAY_MISSING_ONE   = [['2013-03-%02d' % (n + 1), 1] for n in range(31) if n % 7 == 2 and n != 9]
EVERY_MONDAY_DAY_AFTER     = EVERY_MONDAY[:] + [('2013-03-26', 1)]
EVERY_SUNDAY_DAY_AFTER     = EVERY_SUNDAY[:] + [('2013-04-01', 1)]
EVERY_MONDAY_S             = [['2013-03-%02d' % (n + 1), 3] for n in range(31) if n % 7 == 3]
EVERY_TUESDAY_S            = [['2013-03-%02d' % (n + 1), 4] for n in range(31) if n % 7 == 4]
EVERY_SUNDAY_S             = [['2013-03-%02d' % (n + 1), 3] for n in range(31) if n % 7 == 2]
EVERY_SUNDAY_S_MISSING_ONE = [['2013-03-%02d' % (n + 1), 3] for n in range(31) if n % 7 == 2 and n != 9]
EVERY_MONDAY_S_DAY_AFTER   = EVERY_MONDAY[:] + [('2013-03-26', 4)]
EVERY_SUNDAY_S_DAY_AFTER   = EVERY_SUNDAY[:] + [('2013-04-01', 4)]

EVERY_DAY_FIXTURES = (
    PF(func=every_day_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=(),
       expects_none=True),
    PF(func=every_day_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_ALL,
       expects_none=False),
    PF(func=every_day_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_MISSING_ONE,
       expects_none=True),
    PF(func=every_day_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_ONE_ZERO,
       expects_none=True),
    PF(func=every_day_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_DAY_AFTER,
       expects_none=True),
    PF(func=every_day_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=(),
       expects_none=True),
    PF(func=every_day_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_S_ALL,
       expects_none=False),
    PF(func=every_day_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_S_MISSING_ONE,
       expects_none=True),
    PF(func=every_day_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_S_ONE_ZERO,
       expects_none=True),
    PF(func=every_day_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_DAY_S_DAY_AFTER,
       expects_none=True),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-25', 1),),
       expects_none=True),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_MONDAY,
       expects_none=False),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_TUESDAY,
       expects_none=False),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_SUNDAY,
       expects_none=False),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_SUNDAY_MISSING_ONE,
       expects_none=True),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_MONDAY_DAY_AFTER,
       expects_none=True),
    PF(func=every_xday_this_month_nonzero,
       habit=('2013-03-01', 'day'),
       data=EVERY_SUNDAY_DAY_AFTER,
       expects_none=True),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=(('2013-03-25', 1),),
       expects_none=True),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_MONDAY_S,
       expects_none=False),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_TUESDAY_S,
       expects_none=False),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_SUNDAY_S,
       expects_none=False),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_SUNDAY_S_MISSING_ONE,
       expects_none=True),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_MONDAY_S_DAY_AFTER,
       expects_none=True),
    PF(func=every_xday_this_month_succeeding,
       habit=('2013-03-01', 'day'),
       data=EVERY_SUNDAY_S_DAY_AFTER,
       expects_none=True),
)


def test_every_day(self, fixture):
    _test_provider(self, fixture)
helpers.attach_fixture_tests(TestProviders, test_every_day, EVERY_DAY_FIXTURES)
