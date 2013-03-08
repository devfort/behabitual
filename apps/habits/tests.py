from collections import namedtuple
import datetime
import functools

from django.test import TestCase

from apps.accounts.models import User
from apps.habits.models import Habit, TimePeriod

# If, for example, we create a habit on a Tuesday with a resolution of
# 'weekendday', and we try and get the current time period on the Friday, we
# throw an exception because we've not yet reached a valid TimePeriod.
throws = object()

# Weeks start on a Monday
# Months start on the first (surprisingly!)
TIME_PERIOD_FIXTURES = (
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
    ('2013-03-07', '2013-03-09', 'weekendday', 0,      '2013-03-09'),
    ('2013-03-09', '2013-03-10', 'weekday',    throws, None),
    ('2013-03-09', '2013-03-10', 'weekendday', 1,      '2013-03-10'),
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



class HabitRecordingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(email='foo@bar.com')

    def test_cannot_record_negative_value(self):
        today = datetime.date.today()
        h = Habit(start=today, user=self.user, resolution='day')
        t = TimePeriod('day', 0, today)
        with self.assertRaises(ValueError):
            h.record(t, -10)

    def test_must_supply_valid_timepoint(self):
        today = datetime.date.today()
        h = Habit(start=today, user=self.user, resolution='day')
        with self.assertRaises(ValueError):
            h.record(today, 5)

    def test_record_invalid_resolution(self):
        h = Habit.objects.create(start=datetime.date(2013, 3, 4), user=self.user, resolution='day')
        when = h.get_time_period(datetime.date(2013, 3, 4), resolution='week')
        with self.assertRaises(ValueError):
            h.record(when, 5)


def _test_time_period(self, fixture):
    start, when, resolution, result, date = fixture

    start_date = _parse_date(start)
    when_date  = _parse_date(when)

    h = Habit(start=start_date, user=self.user, resolution=resolution)

    if result is throws:
        with self.assertRaises(ValueError):
            h.get_time_period(when_date)
    else:
        tp_date = _parse_date(date)
        t = TimePeriod(resolution, result, tp_date)
        self.assertEqual(t, h.get_time_period(when_date))


for i, fixture in enumerate(TIME_PERIOD_FIXTURES):
    name = 'test_get_time_period_%02d' % i

    def make_test(fix):
        return lambda self: _test_time_period(self, fix)

    setattr(HabitRecordingTests, name, make_test(fixture))


def _test_record(self, fixture):
    start_date = _parse_date(fixture.start)
    h = Habit.objects.create(start=start_date,
                             user=self.user,
                             resolution=fixture.resolution)

    for datum in fixture.data:
        when, value = datum
        when_date = _parse_date(when)
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


for i, fixture in enumerate(RECORD_FIXTURES):
    name = 'test_record_%02d' % i

    def make_test(fix):
        return lambda self: _test_record(self, fix)

    setattr(HabitRecordingTests, name, make_test(fixture))


def _parse_date(iso_string):
    return datetime.datetime.strptime(iso_string, '%Y-%m-%d').date()
