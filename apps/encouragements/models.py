import calendar
from collections import defaultdict
import datetime
import random

from django.db.models import Max

from apps.habits.models import Bucket
from strings import *


class ProviderRegistry(object):
    """
    A registry of encouragement providers that can return a randomly chosen
    encouragement for a habit.
    """

    def __init__(self):
        self._providers = []

    def register(self, func):
        if not callable(func):
            raise ValueError("func must be callable")
        self._providers.append(func)
        return func

    def get_encouragement(self, habit):
        random.shuffle(self._providers)

        for p in self._providers:
            encouragement = p(habit)
            if encouragement:
                return encouragement

        # Fell through: no encouragements
        return None


providers = ProviderRegistry()
get_encouragement = providers.get_encouragement


@providers.register
def static_encouragement_provider(habit):
    """
    Returns a randomly selected static encouragement.
    """
    return random.choice(ENCOURAGEMENT_0)


# 1A. Most periods in a row success
@providers.register
def longest_streak_succeeding(habit):
    if _longest_streak(habit):
        return random.choice(ENCOURAGEMENT_1)
        # return "Longest succeeding streak. You're a carrot!"


# 1B. Most periods in a row non-zero
@providers.register
def longest_streak_nonzero(habit):
    if _longest_streak(habit, success=lambda b: b.value > 0):
        return random.choice(ENCOURAGEMENT_2)
        # return random.choice((
        #     "Longest streak where you did anything. You're a not entirely lazy carrot!",
        # ))


# 2A. The highest value for a time period ... ever ... volume 3
@providers.register
def best_day_ever(habit):
    if habit.resolution in ['week', 'month']:
        return None

    if _best_bucket_ever(habit, habit.resolution):
        return random.choice(ENCOURAGEMENT_3)
        # return "BEST. DAY. EVERRR!"


# 2b. Highest number for a week ever
@providers.register
def best_week_ever(habit):
    if habit.resolution == 'month':
        return None

    if _best_bucket_ever(habit, 'week'):
        return random.choice(ENCOURAGEMENT_4)
        # return "BEST. WEEK. EVERRR!"


# 2c. Highest number for a month ever
@providers.register
def best_month_ever(habit):
    if _best_bucket_ever(habit, 'month'):
        return random.choice(ENCOURAGEMENT_5)
        # return "BEST. MONTH. EVERRR!"


# 4.  For n we consecutively you have entered a zero data point (as opposed
#     to not having entered data)
@providers.register
def streak_of_doom(habit):
    # day - streak of doom where n = 5
    # week - streak of doom where n = 2
    # months n/a
    if habit.resolution in ['day', 'weekday', 'weekendday']:
        doom_threshold = 5
    elif habit.resolution == 'week':
        doom_threshold = 2
    else:
        return None

    buckets = habit.get_buckets(order_by='-index')
    if buckets.count() < doom_threshold:
        return None

    latest = buckets[0]
    buckets = buckets.exclude(index__lt=(latest.index - (doom_threshold - 1)))
    buckets = buckets.filter(value=0)

    if buckets.count() < doom_threshold:
        return None
    else:
        return random.choice(ENCOURAGEMENT_6)


# 5.  The value of the previous consecutive time period is less than the value of this
#     time period
@providers.register
def better_than_before(habit):
    if habit.target_value == 1:
        return None

    buckets = habit.get_buckets(order_by='-index')
    if buckets.count() < 2:
        return None

    if (buckets[0].index - buckets[1].index) != 1:
        return None

    if (buckets[0].value <= buckets[1].value):
        return None

    return random.choice(ENCOURAGEMENT_7)


# 7a. Success if you've done your action every day in the past month.
@providers.register
def every_day_this_month_nonzero(habit):
    if habit.target_value > 1 and _every_day_this_month(habit):
        latest = habit.get_buckets(order_by='-index')[0]
        latest_date = habit.start + datetime.timedelta(days=latest.index)
        return random.choice(ENCOURAGEMENT_8) % {
            'month': calendar.month_name[latest_date.month]
        }


# 7b. Success if you've hit your target every day in the past month.
@providers.register
def every_day_this_month_succeeding(habit):
    if _every_day_this_month(habit, habit.target_value):
        latest = habit.get_buckets(order_by='-index')[0]
        latest_date = habit.start + datetime.timedelta(days=latest.index)
        return random.choice(ENCOURAGEMENT_9) % {
            'month': calendar.month_name[latest_date.month]
        }



# 3a. Only for a daily action if you have done it every {Monday, Tuesday, ...}
#     this month (can only be figured out after the last of those weekdays in
#     a month)
@providers.register
def every_xday_this_month_nonzero(habit):
    if _every_xday_this_month(habit):
        latest = habit.get_buckets(order_by='-index')[0]
        latest_date = habit.start + datetime.timedelta(days=latest.index)
        return random.choice(ENCOURAGEMENT_10) % {
            'day': calendar.day_name[latest_date.weekday()],
            'month': calendar.month_name[latest_date.month]
        }


# 3b. Only for a daily action if you have hit your target every {Monday,
#     Tuesday, ...} this month (can only be figured out after the last of
#     those weekdays in a month)
@providers.register
def every_xday_this_month_succeeding(habit):
    if _every_xday_this_month(habit, habit.target_value):
        latest = habit.get_buckets(order_by='-index')[0]
        latest_date = habit.start + datetime.timedelta(days=latest.index)
        return random.choice(ENCOURAGEMENT_11) % {
            'day': calendar.day_name[latest_date.weekday()],
            'month': calendar.month_name[latest_date.month],
        }

# 6.  "Don't call it a comeback" - n time periods of success, followed by
#     m time periods of failure, followed by k time periods of success
#     (we believe that n and m will be something and something like the
#     ratio of k to m will be at least something)


def _longest_streak(habit, **kwargs):
    streaks = habit.get_streaks(**kwargs)

    # Get most recent streak, if any
    try:
        latest = next(streaks)
    except StopIteration:
        return False

    # If any previous streaks are longer, return None
    for s in streaks:
        if s >= latest:
            return False

    return True


def _best_bucket_ever(habit, resolution):
    buckets = habit.buckets.filter(resolution=resolution).order_by('-index')

    if buckets.count() < 2:
        return False

    latest = buckets[0]
    max_val = buckets.exclude(pk=latest.pk).aggregate(Max('value'))['value__max']

    return latest.value > max_val


def _weekdays_in_month(year, month):
    start, num_days = calendar.monthrange(year, month)
    weekdays = defaultdict(list)
    for i, weekday in enumerate((x + start) % 7 for x in xrange(num_days)):
        weekdays[weekday].append(i + 1)
    return weekdays


def _every_day_this_month(habit, target_value=1):
    if habit.resolution != 'day':
        return False

    buckets = habit.buckets.filter(resolution=habit.resolution).order_by('-index')

    if buckets.count() < 28:
        return False

    latest = buckets[0]
    latest_date = habit.start + datetime.timedelta(days=latest.index)

    # Only proceed to check all buckets this month if we've just entered the
    # last bucket this month. Use == because months aren't monotonically
    # increasing (December -> January).
    next_date = latest_date + datetime.timedelta(days=1)
    if latest_date.month == next_date.month:
        return False

    # Get a list of buckets from the current month
    month_ndays = latest_date.day
    buckets_filtered = buckets.exclude(index__lt=latest.index - (month_ndays - 1))
    buckets_filtered = buckets_filtered.exclude(value__lt=target_value)

    # If you haven't provided data for every day this month, fail
    if buckets_filtered.count() < month_ndays:
        return False

    return True


def _every_xday_this_month(habit, target_value=1):
    if habit.resolution != 'day':
        return False

    buckets = habit.buckets.filter(resolution=habit.resolution).order_by('-index')

    # 4 (or 5) weeks in a month so don't try to calculate this encouragement if
    # we don't have enough data.
    if buckets.count() < 4:
        return False

    latest = buckets[0]
    latest_date = habit.start + datetime.timedelta(days=latest.index)
    month_weekdays = _weekdays_in_month(latest_date.year, latest_date.month)
    last_weekdays = [v[-1] for k, v in month_weekdays.items()]

    try:
        # Set weekday to the integer weekday (Monday=0...Sunday=6) represented
        # by latest_date...
        weekday = last_weekdays.index(latest_date.day)
    except ValueError:
        # ...but fail if it's not one of the last weekdays of the month (e.g.
        # if it's a Wednesday but not the last Wednesday of the month)
        return False

    # Get buckets for all the days in the month which are the same weekday as
    # latest_date.
    month_ndays = latest_date.day
    min_index = latest.index - (month_ndays - 1)
    buckets_filtered = list(Bucket.objects.raw("""
        SELECT * FROM habits_bucket
        WHERE habit_id = %s
        AND resolution = %s
        AND index > %s
        AND (index + %s) %% 7 = %s
        AND value >= %s
    """, [habit.pk,
          habit.resolution,
          min_index,
          habit.start.weekday(),
          weekday,
          target_value]))

    if len(buckets_filtered) < len(month_weekdays[weekday]):
        # Haven't got a bucket for each, so automatically fail
        return False

    return True
