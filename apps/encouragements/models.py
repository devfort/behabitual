import calendar
from collections import defaultdict
import datetime
import random

from django.db.models import Max

from apps.habits.models import Bucket


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
    return random.choice((
        "Fuck YEAH!",
        "AWESOME!",
    ))


# 1A. Most periods in a row success
@providers.register
def longest_streak_succeeding(habit):
    if _longest_streak(habit):
        return "Longest succeeding streak. You're a carrot!"


# 1B. Most periods in a row non-zero
@providers.register
def longest_streak_nonzero(habit):
    if _longest_streak(habit, success=lambda b: b.value > 0):
        return "Longest streak where you did anything. You're a not entirely lazy carrot!"


# 2A. The highest value for a time period ... ever ... volume 3
@providers.register
def best_day_ever(habit):
    if habit.resolution in ['week', 'month']:
        return None

    if _best_bucket_ever(habit, habit.resolution):
        return "BEST. DAY. EVERRR!"


# 2b. Highest number for a week ever
@providers.register
def best_week_ever(habit):
    if habit.resolution == 'month':
        return None

    if _best_bucket_ever(habit, 'week'):
        return "BEST. WEEK. EVERRR!"


# 2c. Highest number for a month ever
@providers.register
def best_month_ever(habit):
    if _best_bucket_ever(habit, 'month'):
        return "BEST. MONTH. EVERRR!"

# 5.  The value of the previous consecutive time period is less than the value of this
#     time period
@providers.register
def better_than_before(habit):
    buckets = habit.get_buckets(order_by='-index')
    if buckets.count() < 2:
        return None

    if (buckets[0].index - buckets[1].index) != 1:
        return None

    if (buckets[0].value <= buckets[1].value):
        return None

    return "FUCK YEAH OTTERS"


# 7.  Success if you've done your action every day in the past month.
@providers.register
def every_day_this_month(habit):
    if habit.resolution != 'day':
        return None

    buckets = habit.buckets.filter(resolution=habit.resolution).order_by('-index')

    if buckets.count() < 28:
        return None

    latest = buckets[0]
    latest_date = habit.start + datetime.timedelta(days=latest.index)

    # Only proceed to check all buckets this month if we've just entered the
    # last bucket this month. Use != because months aren't monotonically
    # increasing (December -> January).
    next_date = latest_date + datetime.timedelta(days=1)
    if latest_date.month == next_date.month:
        return None

    # Get a list of buckets from the current month
    month_ndays = latest_date.day
    buckets_filtered = buckets.exclude(index__lt=latest.index - (month_ndays - 1))

    # If you haven't provided data for every day this month, fail
    if buckets_filtered.count() < month_ndays:
        return None

    for bucket in buckets_filtered:
        if bucket.value == 0:
            return None

    return "Wahey! You've frobbled your wibble every day in %s!" % calendar.month_name[latest_date.month]


def _weekdays_in_month(year, month):
    start, num_days = calendar.monthrange(year, month)
    weekdays = defaultdict(list)
    for i, weekday in enumerate((x + start) % 7 for x in xrange(num_days)):
        weekdays[weekday].append(i + 1)
    return weekdays


# 3. Only for a daily action if you have done it every {Monday, Tuesday, ...} this month
#    (can only be figured out after the last of those weekdays in a month)
@providers.register
def every_xday_this_month(habit):
    if habit.resolution != 'day':
        return None

    buckets = habit.buckets.filter(resolution=habit.resolution).order_by('-index')

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
        return None

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
        AND value > 0
    """, [habit.pk,
          habit.resolution,
          min_index,
          habit.start.weekday(),
          weekday]))

    if len(buckets_filtered) < len(month_weekdays[weekday]):
        # Haven't got a bucket for each, so automatically fail
        return None

    return "Congratulations, you've done your task every %s this %s!" % (
        calendar.day_name[weekday],
        calendar.month_name[latest_date.month])

# 4.  For n we consecutively you have entered a zero data point (as opposed
#     to not having entered data)
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
