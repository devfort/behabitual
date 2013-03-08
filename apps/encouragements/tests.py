from unittest import TestCase
from apps.encouragements.models import Generator

class MockUser(object):
    def __init__(self, id=1):
        self.pk = id


class EncouragementsTest(TestCase):
    def setUp(self):
        self.user = MockUser(4)
        self.providers = (
            lambda user: None,
            lambda user: 'a',
            lambda user: 'b',
        )

    def test_returns_none_with_no_providers(self):
        generator = Generator([])
        self.assertIsNone(generator(self.user))

    def test_returns_the_encouragement_from_a_single_provider(self):
        encouragement = object()
        provider = lambda user: encouragement
        generator = Generator([provider])
        self.assertEqual(encouragement, generator(self.user))

    def test_returns_none_if_the_provider_returns_none(self):
        provider = lambda user: None
        generator = Generator([provider])
        self.assertIsNone(generator(self.user))

    def test_returns_user_derived_encouragements_from_a_provider(self):
        provider = lambda user: user.pk
        generator = Generator([provider])
        self.assertEqual(4, generator(self.user))

    def test_returns_an_encouragement_from_a_set_of_providers(self):
        generator = Generator(self.providers)
        results = [generator(self.user) for i in range(100)]
        self.assertEqual(set(('a', 'b')), set(results))
