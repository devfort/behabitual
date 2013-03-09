import random

from django.db.models import Max

class Generator(object):
    """
    A callable object that returns a random encouragement selected from the
    not-None encouragements returned by its providers.
    """

    def __init__(self, providers=None):
        if providers is None:
            self._providers = []
        else:
            self._providers = list(providers)

    def __call__(self, habit):
        random.shuffle(self._providers)

        for p in self._providers:
            encouragement = p(habit)
            if encouragement:
                return encouragement

        # Fell through: no encouragements
        return None


def static_encouragement_provider(habit):
    """
    Returns a randomly selected static encouragement.
    """
    return random.choice((
        "Fuck YEAH!",
        "AWESOME!",
    ))


# 1A. Most periods in a row success
def most_periods_succeeding_in_a_row(habit):
    streaks = habit.get_streaks()

    # Get most recent streak, if any
    try:
        latest = next(streaks)
    except StopIteration:
        return None

    # If any previous streaks are longer, return None
    for s in streaks:
        if s >= latest:
            return None

    return "WHOO!"

def _best_bucket_ever(habit, resolution):
    buckets = habit.buckets.filter(resolution=resolution).order_by('-index')

    if buckets.count() < 2:
        return False

    latest = buckets[0]
    max_val = buckets.exclude(pk=latest.pk).aggregate(Max('value'))['value__max']

    return latest.value > max_val

# 2A. The highest value for a time period ... ever ... volume 3
def best_day_ever(habit):
    if habit.resolution in ['week', 'month']:
        return None

    if _best_bucket_ever(habit, habit.resolution):
        return "BEST. DAY. EVERRR!"

# 2b. Highest number for a week ever
def best_week_ever(habit):
    if habit.resolution == 'month':
        return None

    if _best_bucket_ever(habit, 'week'):
        return "BEST. WEEK. EVERRR!"


# 2c. Highest number for a month ever
def best_month_ever(habit):
    if _best_bucket_ever(habit, 'month'):
        return "BEST. MONTH. EVERRR!"

# 1B. Most periods in a row non-zero
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

def different_encouragement_provider(habit):
    pass
