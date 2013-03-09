import datetime

def attach_fixture_tests(test_cls, test_func, fixtures):
    """
    For each fixture in the iterable ``fixtures``, attach the test function
    ``test_func`` using that fixture data to the specified test class
    (``test_cls``).
    """
    for i, fixture in enumerate(fixtures):
        name = '%s_%03d' % (test_func.__name__, i)

        def make_test(fix):
            return lambda self: test_func(self, fix)

        setattr(test_cls, name, make_test(fixture))

def parse_isodate(iso_string):
    return datetime.datetime.strptime(iso_string, '%Y-%m-%d').date()
