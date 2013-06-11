from __future__ import division, unicode_literals

from collections import namedtuple
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.humanize.templatetags.humanize import ordinal

from .signals import habit_archived, habit_created, habit_data_recorded

RESOLUTIONS = (
    ('day',        _('day')),
    ('weekday',    _('day on weekdays')),
    ('weekendday', _('day on weekends')),
    ('week',       _('week')),
    ('month',      _('month')),
)

RESOLUTIONS_NO_MONTH = (
    ('day',        _('day')),
    ('weekday',    _('day on weekdays')),
    ('weekendday', _('day on weekends')),
    ('week',       _('week')),
)

def _validate_non_negative(val):
    if val < 0:
        raise ValidationError(u'%s is not greater than or equal to zero' % val)

def _validate_datetime_is_hour(val):
    if val.minute != 0 or val.second != 0 or val.microsecond != 0:
        raise ValidationError(u'%s must have zero-valued minutes, seconds, and microseconds when representing an hour' % val)

TimePeriod_ = namedtuple('TimePeriod', 'resolution index date')

class TimePeriod(TimePeriod_):

    @classmethod
    def from_index(cls, start, resolution, index):
        """Construct a TimePeriod from a start date, a resolution, and a given index"""
        if resolution == 'day':
            date = start + datetime.timedelta(days=index)

        # In order to convert an index to a date for weekdays and weekenddays,
        # we need to work out how many weeks and days to jump forward in time
        # from the start date. This turns out to be quite an interesting
        # problem, and I found it easiest to picture the solution in a table,
        # as shown below.
        #
        # The trick is to use modular arithmetic to count weeks and days from
        # the start of the week in which the start date falls. For start dates
        # that don't fall on a Monday (or a Saturday for weekenddays), we must
        # shift the day and week offsets left by a number of places equivalent
        # to the integer week number of the start date.
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

    def friendly_date(self):
        return self._friendly_date_relative_to(datetime.date.today())

    def _friendly_date_relative_to(self, relative_to):
        if self.resolution == "week":
            return self._friendly_weekly_date(relative_to)
        else:
            return self._friendly_daily_date(relative_to)

    def _friendly_daily_date(self, relative_to):
        delta_days = (relative_to - self.date).days
        if delta_days == 0:
            return _("Today")
        elif delta_days == 1:
            return _("Yesterday")
        elif delta_days < 7:
            # Full day name
            return self.date.strftime("%A")
        else:
            # "March 1st"
            return "%s %s" % (self.date.strftime("%B"), ordinal(self.date.day))

    def _friendly_weekly_date(self, relative_to):
        return "Week of %s %s" % (self.date.strftime("%B"), ordinal(self.date.day))


class Habit(models.Model):
    """
    A habit and its associated data.
    """

    user = models.ForeignKey('accounts.User', related_name='habits')
    resolution = models.CharField(
        max_length=10,
        choices=RESOLUTIONS,
        default='day',
    )
    start = models.DateField()
    target_value = models.PositiveIntegerField(default=1)
    description = models.TextField()
    archived = models.BooleanField(default=False)

    reminder = models.TextField(
        null=True,
        blank=True,
    )
    reminder_days = models.IntegerField(
        validators=[_validate_non_negative],
        default=0,
    )
    reminder_hour = models.IntegerField(
        validators=[_validate_non_negative],
        default=None,
        null=True,
        blank=True
    )
    reminder_last_sent = models.DateTimeField(
        validators=[_validate_datetime_is_hour],
        null=True,
        blank=True
    )
    send_data_collection_emails = models.BooleanField(default=True)

    class Meta:
        # HACK: Use ID as proxy for creation order
        ordering = ['archived', '-id']

    @classmethod
    def scheduled_for_reminder(cls, weekday, hour):
        """
        Get all habits scheduled for a reminder on the given ``weekday`` and
        ``hour``. ``weekday`` should be an integer weekday
        (Monday=0...Sunday=6).
        """
        return cls.objects.raw("""
            SELECT * FROM habits_habit
            WHERE (reminder_days & %s) != 0
            AND reminder_hour = %s
        """, [1 << weekday, hour])

    def save(self, *args, **kwargs):
        # ensure that model field custom validators are always run before saving
        self.full_clean()
        return super(Habit, self).save(*args, **kwargs)

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

    def is_binary(self):
        """
        Returns true if this habit is a yes/no task (versus a how many times you
        did the action)
        """
        return self.target_value == 1

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
        for idx in reversed(range(min_index, time_period.index)):
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

        habit_data_recorded.send(sender=self)

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
        for ident, name in RESOLUTIONS:
            if self.resolution == ident:
                return name

    def set_reminder_schedule(self, weekdays, hour):
        """
        Set the reminder schedule for this habit. Accepts ``weekdays``, a
        list, length 7, with booleanish entries, denoting whether a reminder
        should be sent on each day of the week, and an ``hour`` at which the
        reminder should be sent.

        For example, to send a reminder at 4pm on Mondays, Wednesdays, and
        Fridays:

            days = [True, False, True, False, True, False, False]
            habit.set_reminder_schedule(days, 16)
        """
        if len(weekdays) != 7:
            raise ValueError("weekdays must be a list of length 7")
        if not 0 <= hour < 24:
            raise ValueError("hour must be in the range [0, 24)")

        day_bits = [1 << i if d else 0 for i, d in enumerate(weekdays)]

        self.reminder_days = reduce(lambda x, y: x | y, day_bits)
        self.reminder_hour = hour

    def get_reminder_schedule(self):
        """
        Get the reminder schedule for this habit. For example:

            import calendar
            weekdays, hour = habit.get_reminder_schedule()
            send_on_tuesday = weekdays[calendar.TUESDAY]
        """
        reminder_days = [self.reminder_days & (1 << i) != 0 for i in range(7)]
        return reminder_days, self.reminder_hour

    def __unicode__(self):
        return 'description=%s start=%s resolution=%s' % (
            self.description, self.start, self.resolution
        )


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
        choices=RESOLUTIONS,
        default='day',
    )

    def is_succeeding(self):
        return self.value >= self.habit.target_value

    def __unicode__(self):
        return "resolution=%s index=%s value=%s" % (self.resolution, self.index, self.value)


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
