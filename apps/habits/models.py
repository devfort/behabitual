from __future__ import division

from collections import namedtuple
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

RESOLUTION_NAMES = (
    _('daily'),
    _('on weekdays'),
    _('on weekends'),
    _('weekly'),
    _('monthly'),
)

RESOLUTIONS = (
    'day',
    'weekday',
    'weekendday',
    'week',
    'month',
)


def _validate_non_negative(val):
    if val < 0:
        raise ValidationError(u'%s is not greater than or equal to zero' % val)


TimePeriod = namedtuple('TimePeriod', 'resolution index')


class Habit(models.Model):
    """
    A habit and its associated data.
    """

    user = models.ForeignKey('accounts.User', related_name='habits')
    resolution = models.CharField(
        max_length=10,
        choices=zip(RESOLUTIONS, RESOLUTION_NAMES),
        default='day',
    )
    start = models.DateField()

    def get_current_time_period(self):
        return get_time_period(datetime.date.today())

    def get_time_period(self, when):
        """
        Return the TimePeriod for the date given by ``when``, on the basis of this
        Habit's ``resolution``.
        """
        idx = None

        if self.resolution == 'day':
            idx = (when - self.start).days

        elif self.resolution == 'week':
            start_week = self.start - datetime.timedelta(days=self.start.weekday())
            when_week = when - datetime.timedelta(days=when.weekday())

            idx = (when_week - start_week).days // 7

        elif self.resolution in ['weekday', 'weekendday']:
            start_week = self.start - datetime.timedelta(days=self.start.weekday())
            when_week = when - datetime.timedelta(days=when.weekday())

            num_weekend_days = 2 * (when_week - start_week).days // 7

            # If start is a Sunday, one less weekendday
            if self.start.weekday() == 6:
                num_weekend_days -= 1
            # If when is a Saturday, one more weekendday
            if when.weekday() == 5:
                num_weekend_days += 1
            # If when is a Sunday, two more weekenddays
            if when.weekday() == 6:
                num_weekend_days += 2

            num_days = (when - self.start).days + 1

            if self.resolution == 'weekday':
                idx = num_days - num_weekend_days - 1
                if idx < 0:
                    raise ValueError("No weekdays have passed since start")
            else:
                idx = num_weekend_days - 1
                if idx < 0:
                    raise ValueError("No weekends have passed since start")

        elif self.resolution == 'month':
            start_month = self.start.replace(day=1)
            when_month = when.replace(day=1)

            year_diff = when_month.year - start_month.year
            month_diff = when_month.month - start_month.month

            idx = year_diff * 12 + month_diff

        if idx is not None:
            return TimePeriod(self.resolution, idx)
        else:
            raise RuntimeError("Unhandled resolution: %s" % self.resolution)

    def record(self, when, value):
        if value < 0:
            raise ValueError("value must not be negative")
        if not isinstance(when, TimePeriod):
            raise ValueError("when must be a TimePeriod")

    def __unicode__(self):
        return 'Habit(start=%s resolution=%s)' % (self.start, self.resolution)


class Bucket(models.Model):
    """
    A value in a specified time resolution series for a habit
    """

    habit = models.ForeignKey(Habit, related_name='buckets')
    index = models.IntegerField(
        validators=[_validate_non_negative]
    )
    value = models.IntegerField(
        validators=[_validate_non_negative]
    )
    resolution = models.IntegerField(
        choices=enumerate(RESOLUTIONS),
        default=0,
    )
