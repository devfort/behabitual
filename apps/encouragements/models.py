import random

class Generator(object):
    """
    A callable object that returns a random encouragment selected
    from the not-None encouragements returned by its providers.
    """

    def __init__(self, providers = []):
        self._providers = providers

    def __call__(self, habit):
        try:
            encouragements = [p(habit) for p in self._providers]
            encouragements = [e for e in encouragements if e]
            return random.choice(encouragements)
        except IndexError:
            pass

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
    buckets = habit.get_buckets(order_by='-index')
    if buckets.count() == 0:
        return None
    if not buckets[0].is_succeeding():
        return None
    longest_past_streak = None
    current_streak = 0
    
    for bucket in buckets:
        if bucket.is_succeeding():
            if longest_past_streak is None:
                current_streak += 1
            else:
                longest_past_streak += 1
                if longest_past_streak > current_streak:
                    return None
        else:
            longest_past_streak = 0
    
    return "WHOO!"


# 1B. Most periods in a row non-zero
# 2A. The highest value for a time period ... ever ... volume 3
# 2b. Highest number for a week ever
# 2c. Highest number for a month ever (unless a month granularity)
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
