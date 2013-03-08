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
    ('2013-03-03', '2013-03-05', 'day',        2),
    ('2013-03-03', '2013-03-05', 'weekday',    1),
    ('2013-03-03', '2013-03-05', 'weekendday', 0),
    ('2013-03-03', '2013-03-05', 'week',       1),
    ('2013-03-03', '2013-03-05', 'month',      0),
    ('2013-03-04', '2013-03-05', 'day',        1),
    ('2013-03-04', '2013-03-05', 'weekday',    1),
    ('2013-03-04', '2013-03-05', 'weekendday', throws),
    ('2013-03-04', '2013-03-05', 'week',       0),
    ('2013-03-04', '2013-03-05', 'month',      0),
    ('2013-03-04', '2013-03-11', 'day',        7),
    ('2013-03-04', '2013-03-11', 'weekday',    5),
    ('2013-03-04', '2013-03-11', 'weekendday', 1),
    ('2013-03-04', '2013-03-11', 'week',       1),
    ('2013-03-04', '2013-03-11', 'month',      0),
    ('2013-03-04', '2013-03-16', 'day',        12),
    ('2013-03-04', '2013-03-16', 'weekday',    9),
    ('2013-03-04', '2013-03-16', 'weekendday', 2),
    ('2013-03-04', '2013-03-16', 'week',       1),
    ('2013-03-04', '2013-03-16', 'month',      0),
    ('2013-03-04', '2013-03-28', 'week',       3),
    ('2013-03-04', '2013-03-28', 'month',      0),
    ('2013-03-04', '2013-04-01', 'week',       4),
    ('2013-03-04', '2013-04-01', 'month',      1),
    ('2013-03-07', '2013-03-10', 'weekday',    1),
    ('2013-03-07', '2013-03-09', 'weekday',    1),
    ('2013-03-07', '2013-03-09', 'weekendday', 0),
    ('2013-03-09', '2013-03-10', 'weekday',    throws),
    ('2013-03-09', '2013-03-10', 'weekendday', 1),
)


class HabitRecordingTests(TestCase):

    def test_cannot_record_negative_value(self):
        u = User.objects.create(email='foo@bar.com')
        h = Habit(start=datetime.date.today(), user=u, resolution='day')
        t = TimePeriod('day', 0)
        with self.assertRaises(ValueError):
            h.record(t, -10)

    def test_must_supply_valid_timepoint(self):
        u = User.objects.create(email='foo@bar.com')
        h = Habit(start=datetime.date.today(), user=u, resolution='day')
        t = datetime.date.today()
        with self.assertRaises(ValueError):
            h.record(t, 5)


def _test_time_period(self, fixture):
    start, when, resolution, result = fixture

    start_date = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    when_date  = datetime.datetime.strptime(when, '%Y-%m-%d').date()

    u = User.objects.create(email='foo@bar.com')
    h = Habit(start=start_date, user=u, resolution=resolution)

    if result is throws:
        with self.assertRaises(ValueError):
            h.get_time_period(when_date)
    else:
        t = TimePeriod(resolution, result)
        self.assertEqual(t, h.get_time_period(when_date))


for i, fixture in enumerate(TIME_PERIOD_FIXTURES):
    name = 'test_get_time_period_%02d' % i

    def make_test(fix):
        return lambda self: _test_time_period(self, fix)

    setattr(HabitRecordingTests, name, make_test(fixture))
