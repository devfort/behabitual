from collections import namedtuple
import calendar
import datetime
import functools

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.habits.models import Habit, TimePeriod
from lib import test_helpers as helpers

# If, for example, we create a habit on a Tuesday with a resolution of
# 'weekendday', and we try and get the current time period on the Friday, we
# throw an exception because we've not yet reached a valid TimePeriod.
throws = object()

# Weeks start on a Monday
# Months start on the first (surprisingly!)
TIME_PERIOD_FIXTURES = (
    # (Habit start date, 'Current' date, period, expected index, expected time period start date)
    ('2013-03-03', '2013-03-05', 'day',        2,      '2013-03-05'),
    ('2013-03-03', '2013-03-05', 'weekday',    1,      '2013-03-05'),
    ('2013-03-03', '2013-03-05', 'weekendday', 0,      '2013-03-03'),
    ('2013-03-03', '2013-03-05', 'week',       1,      '2013-03-04'),
    ('2013-03-03', '2013-03-05', 'month',      0,      '2013-03-01'),
    ('2013-03-04', '2013-03-05', 'day',        1,      '2013-03-05'),
    ('2013-03-04', '2013-03-05', 'weekday',    1,      '2013-03-05'),
    ('2013-03-04', '2013-03-05', 'weekendday', throws, None),
    ('2013-03-04', '2013-03-05', 'week',       0,      '2013-03-04'),
    ('2013-03-04', '2013-03-05', 'month',      0,      '2013-03-01'),
    ('2013-03-04', '2013-03-11', 'day',        7,      '2013-03-11'),
    ('2013-03-04', '2013-03-11', 'weekday',    5,      '2013-03-11'),
    ('2013-03-04', '2013-03-11', 'weekendday', 1,      '2013-03-10'),
    ('2013-03-04', '2013-03-11', 'week',       1,      '2013-03-11'),
    ('2013-03-04', '2013-03-11', 'month',      0,      '2013-03-01'),
    ('2013-03-04', '2013-03-16', 'day',        12,     '2013-03-16'),
    ('2013-03-04', '2013-03-16', 'weekday',    9,      '2013-03-15'),
    ('2013-03-04', '2013-03-16', 'weekendday', 2,      '2013-03-16'),
    ('2013-03-04', '2013-03-16', 'week',       1,      '2013-03-11'),
    ('2013-03-04', '2013-03-16', 'month',      0,      '2013-03-01'),
    ('2013-03-04', '2013-03-28', 'week',       3,      '2013-03-25'),
    ('2013-03-04', '2013-03-28', 'month',      0,      '2013-03-01'),
    ('2013-03-04', '2013-04-01', 'week',       4,      '2013-04-01'),
    ('2013-03-04', '2013-04-01', 'month',      1,      '2013-04-01'),
    ('2013-03-07', '2013-03-10', 'weekday',    1,      '2013-03-08'),
    ('2013-03-07', '2013-03-09', 'weekday',    1,      '2013-03-08'),
    ('2013-03-07', '2013-03-13', 'weekday',    4,      '2013-03-13'),
    ('2013-03-07', '2013-03-20', 'weekday',    9,      '2013-03-20'),
    ('2013-03-07', '2013-03-27', 'weekday',   14,      '2013-03-27'),
    ('2013-03-07', '2013-03-23', 'weekday',   11,      '2013-03-22'),
    ('2013-03-07', '2013-03-09', 'weekendday', 0,      '2013-03-09'),
    ('2013-03-09', '2013-03-10', 'weekday',    throws, None),
    ('2013-03-09', '2013-03-10', 'weekendday', 1,      '2013-03-10'),
    ('2013-03-10', '2013-03-10', 'weekendday', 0,      '2013-03-10'),
    ('2013-03-10', '2013-03-16', 'weekendday', 1,      '2013-03-16'),
    ('2013-03-10', '2013-03-17', 'weekendday', 2,      '2013-03-17'),
    ('2013-03-10', '2013-03-23', 'weekendday', 3,      '2013-03-23'),
    ('2013-03-10', '2013-03-26', 'weekendday', 4,      '2013-03-24'),
)

RF = namedtuple('RecordFixture', 'start resolution data checks')
C = namedtuple('Check', 'resolution index value')

RECORD_FIXTURES = (
    RF(start='2013-03-04',
       resolution='day',
       data=(('2013-03-04', 5),),
       checks=(C(resolution='day', index=0, value=5),
               C(resolution='week', index=0, value=5),
               C(resolution='month', index=0, value=5))),
    RF(start='2013-03-04',
       resolution='week',
       data=(('2013-03-04', 3),),
       checks=(C(resolution='day', index=0, value=None),
               C(resolution='week', index=0, value=3),
               C(resolution='month', index=0, value=3))),
    RF(start='2013-03-04',
       resolution='month',
       data=(('2013-03-04', 12),),
       checks=(C(resolution='day', index=0, value=None),
               C(resolution='week', index=0, value=None),
               C(resolution='month', index=0, value=12))),
    RF(start='2013-03-04',
       resolution='day',
       data=(('2013-03-04', 3), ('2013-03-05', 2), ('2013-03-07', 76)),
       checks=(C(resolution='day', index=0, value=3),
               C(resolution='day', index=1, value=2),
               C(resolution='day', index=2, value=None),
               C(resolution='day', index=3, value=76),
               C(resolution='week', index=0, value=81),
               C(resolution='month', index=0, value=81))),
    RF(start='2013-03-04',
       resolution='day',
       data=(('2013-03-08', 3), ('2013-03-13', 4)),
       checks=(C(resolution='day', index=4, value=3),
               C(resolution='day', index=9, value=4),
               C(resolution='week', index=0, value=3),
               C(resolution='week', index=1, value=4),
               C(resolution='month', index=0, value=7))),
    RF(start='2013-03-30',
       resolution='day',
       data=(('2013-03-30', 4), ('2013-04-01', 1)),
       checks=(C(resolution='day', index=0, value=4),
               C(resolution='day', index=1, value=None),
               C(resolution='day', index=2, value=1),
               C(resolution='week', index=0, value=4),
               C(resolution='week', index=1, value=1),
               C(resolution='month', index=0, value=4),
               C(resolution='month', index=1, value=1))),
    # Should skip weekends when calculating bucket indices for weekday
    # resolution:
    RF(start='2013-03-07',
       resolution='weekday',
       data=(('2013-03-07', 3), ('2013-03-11', 4)),
       checks=(C(resolution='weekday', index=0, value=3),
               C(resolution='weekday', index=1, value=None),
               C(resolution='weekday', index=2, value=4),
               C(resolution='week', index=0, value=3),
               C(resolution='week', index=1, value=4),
               C(resolution='month', index=0, value=7))),
    # If I get_time_period for a weekendday with weekday resolution, I should
    # get back the time_period for the most recent weekday:
    RF(start='2013-03-07',
       resolution='weekday',
       data=(('2013-03-07', 3), ('2013-03-10', 4)),
       checks=(C(resolution='weekday', index=0, value=3),
               C(resolution='weekday', index=1, value=4),
               C(resolution='week', index=0, value=7),
               C(resolution='week', index=1, value=None),
               C(resolution='month', index=0, value=7))),
    # Should skip weekdays when calculating bucket indices for weekend
    # resolution:
    RF(start='2013-03-07',
       resolution='weekendday',
       data=(('2013-03-09', 3), ('2013-03-16', 2)),
       checks=(C(resolution='weekendday', index=0, value=3),
               C(resolution='weekendday', index=1, value=None),
               C(resolution='weekendday', index=2, value=2),
               C(resolution='week', index=0, value=3),
               C(resolution='week', index=1, value=2),
               C(resolution='month', index=0, value=5))),
    # If I get_time_period for a weekday with weekendday resolution, I should get
    # back the time_period for the most recent weekendday:
    RF(start='2013-03-07',
       resolution='weekendday',
       data=(('2013-03-11', 128),),
       checks=(C(resolution='weekendday', index=0, value=None),
               C(resolution='weekendday', index=1, value=128),
               C(resolution='week', index=0, value=128),
               C(resolution='week', index=1, value=None),
               C(resolution='month', index=0, value=128))),
)

# Data structure for testing get_streaks. ``habit`` is itself a tuple of
# (start, resolution, target_value).
SF = namedtuple('StreakFixture', 'habit data streaks')

STREAKS_FIXTURES = (
    SF(habit=('2013-03-04', 'day', 1),
       data=(('2013-03-04', 0),),
       streaks=[]),
    SF(habit=('2013-03-04', 'day', 1),
       data=(('2013-03-04', 1),),
       streaks=[1]),
    SF(habit=('2013-03-04', 'day', 1),
       data=(('2013-03-04', 1), ('2013-03-05', 2), ('2013-03-06', 0), ('2013-03-07', 1)),
       streaks=[1, 2]),
    SF(habit=('2013-03-04', 'day', 3),
       data=(('2013-03-04', 2), ('2013-03-05', 3), ('2013-03-06', 1), ('2013-03-07', 6)),
       streaks=[1, 1]),
    # Streaks should respect expected gaps (e.g. weekends in weekday
    # resolution habits)
    SF(habit=('2013-03-04', 'weekday', 3),
       data=(('2013-03-07', 3), ('2013-03-08', 3), ('2013-03-11', 4), ('2013-03-12', 6)),
       streaks=[4]),
    SF(habit=('2013-03-04', 'week', 3),
       data=(('2013-03-04', 1), ('2013-03-05', 2), ('2013-03-11', 4)),
       streaks=[2]),
)

# create habit of a (particular date, resolution) + set[interval value pairs for
# data that has been entered], date, expected list of intervals
RTPT = namedtuple('RecentTimePeriodTest', 'start resolution data date expected')

RECENT_TIME_PERIODS_FIXTURES = (
    # Habit started 1st March, daily, no data has been entered.
    # Today is 5th March.
    # Therefore, we expect data from the five days between (and including) 1st
    # and 5th March.
    RTPT('2013-03-01', 'day', (), '2013-03-05', [4,3,2,1,0]),
    # Habit started 1st March, daily, data has been entered for March 3rd.
    # Today is 5th March.
    # Therefore we expect data for the 4th, and the 5th of March (i.e. the 3rd
    # and 4th time period).
    # We have written off the 0th and 1st time period (1st, 2nd March).
    RTPT('2013-03-01', 'day', (('2013-03-03',1),), '2013-03-05', [4,3]),
    # Habit started 1st March, daily, data has been entered for 5th March.
    # Today is 5th March.
    # Therefore, we consider ourselves to be up-to-date with data.
    RTPT('2013-03-01', 'day', (('2013-03-05',1),), '2013-03-05', []),
    # Habit started 1st May, weekly, no data has been entered.
    # Today is 2nd May.
    # Therefore we expect data for the 0th week.
    # This is the logic I think is incorrect.
    # The TimePeriod returned is this:
    # [TimePeriod(resolution='week', index=0, date=datetime.date(2013, 4, 29))]
    # i.e. it expects data for the w/c 29th April. I say that's wrong.
    RTPT('2013-05-01', 'week', (), '2013-05-02', [0]),
    # Habit started 1st May, weekly, data has been entered for 2nd week
    # Today is 29th May.
    # Therefore we expect data for the 3rd and 4th week
    # I think it should be only the 3rd week
    RTPT('2013-05-01', 'week', (('2013-05-13',1),), '2013-05-29', [4,3]),
    # Habit started 1st May, weekly.
    # Data has been entered for 1st week, 2nd week and 4th week
    # Today is 18th June.
    # Therefore we expect data for the 5th, 6th and 7th week
    # I think it should be only the 5th and 6th
    RTPT('2013-05-01', 'week', (('2013-05-06',1),('2013-05-13',1),('2013-05-27',1)), '2013-06-18', [7,6,5]),
)

TPFNF = namedtuple('TimePeriodFriendlyNameFixture', 'start resolution relative expected')

TIME_PERIOD_FRIENDLY_NAME_FIXTURES = (
    TPFNF('2013-03-05', 'day', '2013-03-05', 'Today'),
    TPFNF('2013-03-04', 'day', '2013-03-05', 'Yesterday'),
    TPFNF('2013-03-03', 'day', '2013-03-05', 'Sunday'),
    TPFNF('2013-03-02', 'day', '2013-03-05', 'Saturday'),
    TPFNF('2013-03-01', 'day', '2013-03-05', 'Friday'),
    TPFNF('2013-02-28', 'day', '2013-03-05', 'Thursday'),
    TPFNF('2013-02-27', 'day', '2013-03-05', 'Wednesday'),
    TPFNF('2013-02-26', 'day', '2013-03-05', 'February 26th'),
    TPFNF('2013-03-05', 'day', '2013-03-15', 'March 5th'),
    TPFNF('2013-03-05', 'week', '2013-03-15', 'Week of March 5th'),
)

SCHEDULE_MONDAYS     = [n == 0 for n in range(7)]
SCHEDULE_MON_WED_FRI = [n % 2 == 0 and n != 6 for n in range(7)]
SCHEDULE_WEEKENDS    = [n > 4 for n in range(7)]

class HabitTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')

    def test_cannot_record_negative_value(self):
        today = datetime.date.today()
        h = Habit(description="Brush my teeth",
                  start=today,
                  user=self.user,
                  resolution='day')
        t = TimePeriod('day', 0, today)
        with self.assertRaises(ValueError):
            h.record(t, -10)

    def test_must_supply_valid_timepoint(self):
        today = datetime.date.today()
        h = Habit(description="Brush my teeth",
                  start=today,
                  user=self.user,
                  resolution='day')
        with self.assertRaises(ValueError):
            h.record(today, 5)

    def test_record_invalid_resolution(self):
        h = Habit.objects.create(description="Brush my teeth",
                                 start=datetime.date(2013, 3, 4),
                                 user=self.user,
                                 resolution='day')
        when = h.get_time_period(datetime.date(2013, 3, 4), resolution='week')
        with self.assertRaises(ValueError):
            h.record(when, 5)

    def test_is_up_to_date(self):
        h = Habit.objects.create(description="Brush my teeth",
                  start=datetime.date.today(),
                  user=self.user,
                  resolution='day')
        self.assertEquals(False, h.is_up_to_date())

        h.record(h.get_time_period(h.start), 17)
        self.assertEquals(True, h.is_up_to_date())

    def test_set_reminder_schedule_validation(self):
        mondays = [n == 0 for n in range(7)]

        h = Habit()

        # Can't specify a negative hour
        with self.assertRaises(ValueError):
            h.set_reminder_schedule(mondays, -2)

        # Can't specify an hour > 23
        with self.assertRaises(ValueError):
            h.set_reminder_schedule(mondays, 24)

        # Can't give a list of length != 7
        with self.assertRaises(ValueError):
            h.set_reminder_schedule(mondays[:-1], 12)
        with self.assertRaises(ValueError):
            h.set_reminder_schedule(mondays + [True], 12)

    def test_set_reminder_schedule(self):
        h = Habit()

        h.set_reminder_schedule(SCHEDULE_MONDAYS, 12)
        self.assertEquals(h.reminder_days, 1)
        self.assertEquals(h.reminder_hour, 12)

        h.set_reminder_schedule(SCHEDULE_MON_WED_FRI, 3)
        self.assertEquals(h.reminder_days, 1 | 4 | 16)
        self.assertEquals(h.reminder_hour, 3)

        h.set_reminder_schedule(SCHEDULE_WEEKENDS, 0)
        self.assertEquals(h.reminder_days, 32 | 64)
        self.assertEquals(h.reminder_hour, 0)

    def test_get_reminder_schedule(self):
        h = Habit()

        h.reminder_days = 1
        h.reminder_hour = 12
        weekdays, hour = h.get_reminder_schedule()
        self.assertEquals(SCHEDULE_MONDAYS, weekdays)
        self.assertEquals(hour, 12)

        h.reminder_days = 1 | 4 | 16
        h.reminder_hour = 3
        weekdays, hour = h.get_reminder_schedule()
        self.assertEquals(SCHEDULE_MON_WED_FRI, weekdays)
        self.assertEquals(hour, 3)

        h.reminder_days = 32 | 64
        h.reminder_hour = 0
        weekdays, hour = h.get_reminder_schedule()
        self.assertEquals(SCHEDULE_WEEKENDS, weekdays)
        self.assertEquals(hour, 0)

    def _scheduled(self, weekday, hour):
        return list(Habit.scheduled_for_reminder(weekday, hour))

    def test_scheduled_for_reminder_no_schedule(self):
        h = Habit.objects.create(user=self.user,
                                 start=datetime.date(2013, 3, 4),
                                 description='Do a thing. On a day.')

        self.assertEquals(len(self._scheduled(calendar.MONDAY,  12)), 0)
        self.assertEquals(len(self._scheduled(calendar.MONDAY,  6)),  0)
        self.assertEquals(len(self._scheduled(calendar.TUESDAY, 6)),  0)

    def test_scheduled_for_reminder_mondays(self):
        h = Habit(user=self.user,
                  start=datetime.date(2013, 3, 4),
                  description='Do a thing. On a day.')
        h.set_reminder_schedule(SCHEDULE_MONDAYS, 12)
        h.save()

        self.assertEquals(len(self._scheduled(calendar.MONDAY,  12)),   1)
        self.assertEquals(self._scheduled(calendar.MONDAY,      12)[0], h)
        self.assertEquals(len(self._scheduled(calendar.MONDAY,  6)),    0)
        self.assertEquals(len(self._scheduled(calendar.TUESDAY, 12)),   0)

    def test_scheduled_for_reminder_mon_wed_fri(self):
        h = Habit(user=self.user,
                  start=datetime.date(2013, 3, 4),
                  description='Do a thing. On a day.')
        h.set_reminder_schedule(SCHEDULE_MON_WED_FRI, 15)
        h.save()

        self.assertEquals(len(self._scheduled(calendar.MONDAY,    15)),   1)
        self.assertEquals(self._scheduled(calendar.MONDAY,        15)[0], h)
        self.assertEquals(len(self._scheduled(calendar.MONDAY,    6)),    0)
        self.assertEquals(len(self._scheduled(calendar.TUESDAY,   15)),   0)
        self.assertEquals(self._scheduled(calendar.WEDNESDAY,     15)[0], h)
        self.assertEquals(len(self._scheduled(calendar.WEDNESDAY, 6)),    0)

    def test_scheduled_for_reminder_weekends(self):
        h = Habit(user=self.user,
                  start=datetime.date(2013, 3, 4),
                  description='Do a thing. On a day.')
        h.set_reminder_schedule(SCHEDULE_WEEKENDS, 0)
        h.save()

        self.assertEquals(len(self._scheduled(calendar.MONDAY,   0)),   0)
        self.assertEquals(len(self._scheduled(calendar.SATURDAY, 6)),   0)
        self.assertEquals(len(self._scheduled(calendar.SATURDAY, 0)),   1)
        self.assertEquals(self._scheduled(calendar.SATURDAY,     0)[0], h)

    def test_scheduled_for_reminder_multiple_habits(self):
        h1 = Habit(user=self.user,
                   start=datetime.date(2013, 3, 4),
                   description='Habit 1')
        h1.set_reminder_schedule(SCHEDULE_MONDAYS, 16)
        h1.save()
        h2 = Habit(user=self.user,
                   start=datetime.date(2013, 3, 4),
                   description='Habit 2')
        h2.set_reminder_schedule(SCHEDULE_MON_WED_FRI, 16)
        h2.save()

        self.assertEquals(len(self._scheduled(calendar.MONDAY,    0)),  0)
        self.assertEquals(len(self._scheduled(calendar.MONDAY,    16)), 2)
        self.assertEquals(len(self._scheduled(calendar.WEDNESDAY, 0)),  0)
        self.assertEquals(len(self._scheduled(calendar.WEDNESDAY, 16)), 1)

    def test_reminder_last_sent(self):
        h = Habit(user=self.user,
                  start=datetime.date(2013, 3, 4),
                  description='Test my reminders')

        d = timezone.now()
        h.reminder_last_sent = d
        with self.assertRaises(ValidationError):
            h.save()

        d = d.replace(minute=0, second=0, microsecond=0)
        h.reminder_last_sent = d
        h.save()
        self.assertEqual(h.reminder_last_sent, d)

class TimePeriodTests(TestCase):
    pass

def test_time_period_from_date(self, fixture):
    start, when, resolution, result, date = fixture

    start_date = helpers.parse_isodate(start)
    when_date  = helpers.parse_isodate(when)

    if result is throws:
        with self.assertRaises(ValueError):
            TimePeriod.from_date(start_date, resolution, when_date)
    else:
        tp_date = helpers.parse_isodate(date)
        exp = TimePeriod(resolution, result, tp_date)
        self.assertEqual(TimePeriod.from_date(start_date, resolution, when_date), exp)

helpers.attach_fixture_tests(TimePeriodTests, test_time_period_from_date, TIME_PERIOD_FIXTURES)

def test_time_period_from_index(self, fixture):
    start, when, resolution, result, date = fixture

    start_date = helpers.parse_isodate(start)
    when_date  = helpers.parse_isodate(when)

    if result is not throws:
        tp_date = helpers.parse_isodate(date)
        exp = TimePeriod(resolution, result, tp_date)
        self.assertEqual(TimePeriod.from_index(start_date, resolution, result), exp)

helpers.attach_fixture_tests(TimePeriodTests, test_time_period_from_index, TIME_PERIOD_FIXTURES)

def test_time_period_friendly_name(self, fixture):

    start_date = helpers.parse_isodate(fixture.start)
    relative = helpers.parse_isodate(fixture.relative)

    tp = TimePeriod(fixture.resolution, 0, start_date)
    got = tp._friendly_date_relative_to(relative)
    self.assertEqual(fixture.expected, got)

helpers.attach_fixture_tests(TimePeriodTests, test_time_period_friendly_name, TIME_PERIOD_FRIENDLY_NAME_FIXTURES)

def test_recent_unentered_time_periods(self, fixture):
    # start, resolution, data, date, expected = fixture
    start_date = helpers.parse_isodate(fixture.start)
    h = Habit.objects.create(description="Tangle my wobble",
                             start=start_date,
                             user=self.user,
                             resolution=fixture.resolution,
                             target_value=1)

    for datum in fixture.data:
        when, value = datum
        when_date = helpers.parse_isodate(when)
        tp = h.get_time_period(when_date)
        h.record(tp, value)


    periods = h.get_unentered_time_periods(helpers.parse_isodate(fixture.date))
    self.assertEquals(map(lambda p: p.index, periods), fixture.expected)

helpers.attach_fixture_tests(HabitTests, test_recent_unentered_time_periods, RECENT_TIME_PERIODS_FIXTURES)

def test_record(self, fixture):
    start_date = helpers.parse_isodate(fixture.start)
    h = Habit.objects.create(description="Brush my teeth",
                             start=start_date,
                             user=self.user,
                             resolution=fixture.resolution)

    for datum in fixture.data:
        when, value = datum
        when_date = helpers.parse_isodate(when)
        tp = h.get_time_period(when_date)
        h.record(tp, value)

    for check in fixture.checks:
        # Assert the bucket does not exist
        if check.value is None:
            buckets = h.buckets.filter(resolution=check.resolution,
                                       index=check.index)
            self.assertEqual(buckets.count(), 0)
        else:
            bucket = h.buckets.get(resolution=check.resolution,
                                   index=check.index)
            self.assertEqual(bucket.value, check.value)

helpers.attach_fixture_tests(HabitTests, test_record, RECORD_FIXTURES)


def test_get_streaks(self, fixture):
    start, resolution, target_value = fixture.habit
    start_date = helpers.parse_isodate(start)
    h = Habit.objects.create(description="Foo my bar",
                             start=start_date,
                             user=self.user,
                             resolution=resolution,
                             target_value=target_value)

    for datum in fixture.data:
        when, value = datum
        when_date = helpers.parse_isodate(when)
        tp = h.get_time_period(when_date)
        h.record(tp, value)

    self.assertEqual(list(h.get_streaks()), fixture.streaks)

helpers.attach_fixture_tests(HabitTests, test_get_streaks, STREAKS_FIXTURES)
