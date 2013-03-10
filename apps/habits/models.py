from __future__ import division, unicode_literals

from collections import namedtuple
import datetime

from django.core.exceptions import ValidationError
from django.db import models
import django.dispatch
from django.utils.translation import ugettext_lazy as _

record_habit_data = django.dispatch.Signal()
record_habit_archived = django.dispatch.Signal()
record_habit_created = django.dispatch.Signal()

RESOLUTION_NAMES = (
    _('day'),
    _('day on weekdays'),
    _('day on weekends'),
    _('week'),
)

RESOLUTIONS = (
    'day',
    'weekday',
    'weekendday',
    'week',
)

RESOLUTION_CHOICES = zip(RESOLUTIONS, RESOLUTION_NAMES)


def _validate_non_negative(val):
    if val < 0:
        raise ValidationError(u'%s is not greater than or equal to zero' % val)


TimePeriod_ = namedtuple('TimePeriod', 'resolution index date')

def _num_weekend_days_between(from_date, to_date):
    from_week = from_date - datetime.timedelta(days=from_date.weekday())
    to_week = to_date - datetime.timedelta(days=to_date.weekday())

    num_weekend_days = 2 * (to_week - from_week).days // 7

    # If start is a Sunday, one less weekendday
    if from_date.weekday() == 6:
        num_weekend_days -= 1
    # If when is a Saturday, one more weekendday
    if to_date.weekday() == 5:
        num_weekend_days += 1
    # If when is a Sunday, two more weekenddays
    if to_date.weekday() == 6:
        num_weekend_days += 2

    return num_weekend_days


class TimePeriod(TimePeriod_):

    @classmethod
    def from_index(cls, start, resolution, index):
        """Construct a TimePeriod from a start date, a resolution, and a given index"""
        if resolution == 'day':
            date = start + datetime.timedelta(days=index)

        # In order to convert an index to a date for weekdays and weekenddays,
        # we need to work out how many weeks and days to jump forward in time
        # from the start date. This turns out to be quite an interesting
        # problem, and I found it easiest to picture the problem in a table,
        # as shown below.
        #
        # The trick is to use modular arithmetic to count weeks and days from
        # the start of the week in which the start date falls. For start dates
        # that don't fall on a Monday (or a Saturday for weekenddays), we must
        # shift the offsets left by a number of places equivalent to the
        # integer week number of the start date.
        #
        # For example, for weekdays, starting on a Tuesday, the offset is 1,
        # so:
        #
        #   M T W T F S S M T W T F S S M ...
        #   index:
        #     0 1 2 3     4 5 6 7 8     9 ...
        #   week_offset:
        #   0 0 0 0 0     1 1 1 1 1     2 ...
        #   day_offset:
        #   0 1 2 3 4     0 1 2 3 4     0 ...
        #
        # A similar diagram for weekenddays (starting on a Sunday):
        #
        #   S S M T W T F S S M ...
        #   index:
        #     0           1 2   ...
        #   week_offset:
        #   0 0           1 1   ...
        #   day_offset:
        #   0 1           0 1   ...
        #
        elif resolution == 'weekendday':
            if start.weekday() < 5:
                # Skip forward to Saturday
                date = start + datetime.timedelta(days=5 - start.weekday())
                offset = 0
            else:
                date = start - datetime.timedelta(days=start.weekday() - 5)
                offset = start.weekday() - 5

            week_offset = (index + offset) // 2
            day_offset = (index + offset) % 2

            date += datetime.timedelta(days=7 * week_offset + day_offset)

        elif resolution == 'weekday':
            if start.weekday() >= 5:
                # Skip forward to Monday
                date = start + datetime.timedelta(days=7 - start.weekday())
                offset = 0
            else:
                date = start - datetime.timedelta(days=start.weekday())
                offset = start.weekday()

            week_offset = (index + offset) // 5
            day_offset = (index + offset) % 5

            date += datetime.timedelta(days=7 * week_offset + day_offset)

        elif resolution == 'week':
            start_week = start - datetime.timedelta(days=start.weekday())
            date = start_week + datetime.timedelta(days=index * 7)

        elif resolution == 'month':
            year = start.year + index // 12
            month = start.month + index % 12
            date = datetime.date(year, month, 1)

        else:
            raise RuntimeError("Unhandled resolution: %s" % resolution)

        return cls(resolution, index, date)

    @classmethod
    def from_date(cls, start, resolution, date):
        """Construct a TimePeriod from a start date, a resolution, and a given date"""
        tp_index = None
        tp_date = None

        if resolution == 'day':
            tp_index = (date - start).days
            tp_date = date

        elif resolution == 'week':
            start_week = start - datetime.timedelta(days=start.weekday())
            date_week = date - datetime.timedelta(days=date.weekday())

            tp_index = (date_week - start_week).days // 7
            tp_date = date_week

        elif resolution in ['weekday', 'weekendday']:
            start_week = start - datetime.timedelta(days=start.weekday())
            date_week = date - datetime.timedelta(days=date.weekday())

            num_days = (date - start).days + 1
            num_weekend_days = _num_weekend_days_between(start, date)

            if resolution == 'weekday':
                tp_index = num_days - num_weekend_days - 1
                if tp_index < 0:
                    raise ValueError("No weekdays have passed since start")
                if date.weekday() < 5:
                    tp_date = date
                else:
                    # Skip back to Friday
                    tp_date = date - datetime.timedelta(days=date.weekday() - 4)
            else:
                tp_index = num_weekend_days - 1
                if tp_index < 0:
                    raise ValueError("No weekends have passed since start")
                if date.weekday() >= 5:
                    tp_date = date
                else:
                    # Skip back to Sunday
                    tp_date = date - datetime.timedelta(days=date.weekday() + 1)

        elif resolution == 'month':
            start_month = start.replace(day=1)
            date_month = date.replace(day=1)

            year_diff = date_month.year - start_month.year
            month_diff = date_month.month - start_month.month

            tp_index = year_diff * 12 + month_diff
            tp_date = date_month

        else:
            raise RuntimeError("Unhandled resolution: %s" % resolution)

        return cls(resolution, tp_index, tp_date)


class Habit(models.Model):
    """
    A habit and its associated data.
    """

    user = models.ForeignKey('accounts.User', related_name='habits')
    resolution = models.CharField(
        max_length=10,
        choices=RESOLUTION_CHOICES,
        default='day',
    )
    start = models.DateField()
    target_value = models.PositiveIntegerField(default=1)
    description = models.TextField()
    archived = models.BooleanField(default=False)

    class Meta:
        # HACK: Use ID as proxy for creation order
        ordering = ['archived', '-id']

    def get_current_time_period(self):
        return self.get_time_period(datetime.date.today())

    def get_time_period(self, when, resolution=None):
        """
        Return the TimePeriod for the date given by ``when``, on the basis of
        the passed ``resolution`` (defaults to the Habit's ``resolution``).
        """
        if resolution is None:
            resolution = self.resolution

        return TimePeriod.from_date(self.start, resolution, when)

    def is_up_to_date(self):
        time_period = self.get_current_time_period()
        return self.get_buckets().filter(index=time_period.index).count() != 0

    def get_recent_unentered_time_periods(self):
        return self.get_unentered_time_periods(datetime.date.today())

    def get_unentered_time_periods(self, when):
        time_period = self.get_time_period(when)
        buckets = self.get_buckets(order_by='-index')
        if buckets.count() == 0:
            min_index = 0
        else:
            min_index = buckets[0].index + 1

        ret = []
        for idx in reversed(range(min_index, time_period.index + 1)):
            ret.append(TimePeriod.from_index(self.start, self.resolution, idx))

        return ret

    def record(self, time_period, value):
        """
        Record a data point for the habit in a time period and all lower
        resolution time periods.
        """

        if value < 0:
            raise ValueError("value must not be negative")
        if not isinstance(time_period, TimePeriod):
            raise ValueError("when must be a TimePeriod")
        if time_period.resolution != self.resolution:
            raise ValueError("passed TimePeriod must have resolution matching Habit")

        _increment_bucket(self, time_period, value)

        if self.resolution in ['day', 'weekday', 'weekendday']:
            tp = self.get_time_period(time_period.date, 'week')
            _increment_bucket(self, tp, value)

        if self.resolution != 'month':
            tp = self.get_time_period(time_period.date, 'month')
            _increment_bucket(self, tp, value)

        record_habit_data.send(sender=self)

    def get_buckets(self, order_by='index'):
        return self.buckets.filter(
            resolution=self.resolution,
        ).order_by(order_by)

    def get_streaks(self, success=lambda b: b.is_succeeding()):
        """
        Return a generator yielding the length of each streak satisfying the
        condition given by the ``success`` callable (a function taking a
        bucket and returning a boolean).
        """
        buckets = self.get_buckets(order_by='-index')
        if buckets.count() == 0:
            return

        streak = 0
        previous_index = buckets[0].index + 1

        for bucket in buckets:
            if bucket.index != previous_index - 1:
                # Buckets not consecutive. Yield previous streak (if any) and reset.
                if streak:
                    yield streak
                streak = 0

            if success(bucket):
                streak += 1

            else:
                # Bucket failing. Yield previous streak (if any) and reset.
                if streak:
                    yield streak
                streak = 0

            previous_index = bucket.index

        if streak:
            yield streak

    def get_resolution_name(self):
        resolution_index = RESOLUTIONS.index(self.resolution)
        return RESOLUTION_NAMES[resolution_index]

    def __unicode__(self):
        return 'description=%s start=%s resolution=%s' % (
            self.description, self.start, self.resolution
        )

def _increment_bucket(habit, time_period, value):
    try:
        b = habit.buckets.get(resolution=time_period.resolution,
                              index=time_period.index)
    except Bucket.DoesNotExist:
        b = Bucket(habit=habit,
                   resolution=time_period.resolution,
                   index=time_period.index)

    b.value += value
    b.save()
    return b

class Bucket(models.Model):
    """
    A value in a specified time resolution series for a habit
    """
    class Meta(object):
        unique_together = ['habit', 'resolution', 'index']

    habit = models.ForeignKey(Habit, related_name='buckets')
    index = models.IntegerField(
        validators=[_validate_non_negative]
    )
    value = models.IntegerField(
        validators=[_validate_non_negative],
        default=0,
    )
    resolution = models.CharField(
        max_length=10,
        choices=zip(RESOLUTIONS, RESOLUTION_NAMES),
        default='day',
    )

    def is_succeeding(self):
        return self.value >= self.habit.target_value

    def __unicode__(self):
        return "resolution=%s index=%s value=%s" % (self.resolution, self.index, self.value)
