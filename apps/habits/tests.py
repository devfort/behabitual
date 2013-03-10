from collections import namedtuple
import datetime
import functools

from django.test import TestCase
from django_webtest import WebTest
from django.core.urlresolvers import reverse

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
    RTPT('2013-03-01', 'day', tuple(), '2013-03-05', [4,3,2,1,0]),
    RTPT('2013-03-01', 'day', (('2013-03-03',1),), '2013-03-05', [4,3]),
    RTPT('2013-03-01', 'day', (('2013-03-05',1),), '2013-03-05', []),
)

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


def test_get_time_period(self, fixture):
    start, when, resolution, result, date = fixture

    start_date = helpers.parse_isodate(start)
    when_date  = helpers.parse_isodate(when)

    h = Habit(description="Brush my teeth",
              start=start_date,
              user=self.user,
              resolution=resolution)

    if result is throws:
        with self.assertRaises(ValueError):
            h.get_time_period(when_date)
    else:
        tp_date = helpers.parse_isodate(date)
        t = TimePeriod(resolution, result, tp_date)
        self.assertEqual(t, h.get_time_period(when_date))

helpers.attach_fixture_tests(HabitTests, test_get_time_period, TIME_PERIOD_FIXTURES)

def test_recent_unentered_time_periods(self, fixture):
    # start, resolution, data, date, expected = fixture
    start_date = helpers.parse_isodate(fixture.start)
    h = Habit.objects.create(start=start_date,
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
    h = Habit.objects.create(start=start_date,
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

class HabitArchiveViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='someone@example.com', password='123456'
        )
        self.client.login(email='someone@example.com', password='123456')
        self.habit = Habit.objects.create(
            description="Brush my teeth",
            start=datetime.date.today(),
            user=self.user,
            resolution='day'
        )

    def test_archive_habit(self):
        response = self.client.post(reverse('habit_archive', args=[self.habit.id]), {
            'archive': '1'
        }, HTTP_REFERER=reverse('homepage'))
        self.assertRedirects(response, reverse('homepage'))

        self.habit = Habit.objects.get(pk=self.habit.pk)

        self.assertEquals(True, self.habit.archived)

    def test_unarchive_habit(self):
        self.habit.archived = True
        self.habit.save()
        response = self.client.post(reverse('habit_archive', args=[self.habit.id]), {
            'archive': '0'
        })
        self.assertRedirects(response, reverse('habit', args=[self.habit.id]))

        self.habit = Habit.objects.get(pk=self.habit.pk)

        self.assertEquals(False, self.habit.archived)

class HabitRecordViewTest(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = User.objects.create_user(
            email='someone@example.com', password='123456'
        )
        self.habit = Habit.objects.create(
            description="Brush my teeth",
            start=datetime.date.today(),
            user=self.user,
            resolution='day'
        )

    def test_record_get(self):
        # Simple test to make sure the record view shows without error
        self.habit.record(self.habit.get_time_period(self.habit.start), 2)
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        self.assertRedirects(response, reverse('homepage'))

    def test_record_get_no_data_needed(self):
        # Simple test to make sure the record view shows without error
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')

    def test_record_post(self):
        time_period = self.habit.get_current_time_period()
        params = {
            '0-date': time_period.date,
            '0-value': 2,
        }
        response = self.app.post(reverse('habit_record', args=[self.habit.id]), params, user='someone@example.com')
        self.assertRedirects(response, reverse('habit_encouragement', args=[self.habit.id]))

        bucket = self.habit.get_buckets().get(index=time_period.index)
        self.assertEquals(2, bucket.value)

    def test_record_post_two(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=1),
            user=self.user,
            resolution='day'
        )
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        form = response.form # FIXME: will break if other forms added to page or chrome
        form.set('0-value', 1)
        form.set('1-value', 2)
        resp = form.submit()
        self.assertEqual(302, resp.status_code)
        self.assertEqual('http://localhost:80' + reverse('habit_encouragement', args=[self.habit.id]), resp.headers['Location'])

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(1, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(2, bucket.value)

    def test_record_post_two_not_at_start(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=2),
            user=self.user,
            resolution='day'
        )
        self.habit.record(self.habit.get_time_period(self.habit.start), 17)
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        form = response.form # FIXME: will break if other forms added to page or chrome
        with self.assertRaises(AssertionError):
            # not in the form because data already exists
            form.set('0-value', 1000)
        form.set('1-value', 41)
        form.set('2-value', 108)
        resp = form.submit()
        self.assertEqual(302, resp.status_code)
        self.assertEqual('http://localhost:80' + reverse('habit_encouragement', args=[self.habit.id]), resp.headers['Location'])

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(17, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(41, bucket.value)
        bucket = self.habit.get_buckets().get(index=2)
        self.assertEquals(108, bucket.value)

    def test_record_post_ignore_existing_buckets(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=1),
            user=self.user,
            resolution='day'
        )
        self.habit.record(self.habit.get_time_period(self.habit.start), 17)
        time_period = self.habit.get_current_time_period()
        params = {
            '0-date': time_period.date,
            '0-value': 2,
            '1-date': time_period.date,
            '1-value': 2,
        }
        response = self.app.post(reverse('habit_record', args=[self.habit.id]), params, user='someone@example.com')
        self.assertRedirects(response, reverse('habit_encouragement', args=[self.habit.id]))

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(17, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(2, bucket.value)
