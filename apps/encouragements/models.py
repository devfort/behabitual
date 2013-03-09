import random

from django.db.models import Max


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



# 3.  Only for a daily action if you have done it every (day) this month
#     (can only be figured out after that day in a month)
# 4.  For n we consecutively you have entered a zero data point (as opposed
#     to not having entered data)
# 5.  The value of the previous time period is less than the value of this
#     time period
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
