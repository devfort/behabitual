import random

class Generator(object):
    """
    A callable object that returns a random encouragment selected
    from the not-None encouragements returned by its providers.
    """

    def __init__(self, providers = []):
        self._providers = providers

    def __call__(self, user):
        try:
            encouragements = [p(user) for p in self._providers]
            encouragements = [e for e in encouragements if e]
            return random.choice(encouragements)
        except IndexError:
            pass

def static_encouragement_provider(user):
    """
    Returns a randomly selected static encouragement.
    """
    return random.choice((
        "Fuck YEAH!",
        "AWESOME!",
    ))
