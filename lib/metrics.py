from django.conf import settings

from statsd import StatsdClient

statsd = StatsdClient(host=getattr(settings, 'STATSD_HOST', None),
                      port=getattr(settings, 'STATSD_PORT', None),
                      prefix=getattr(settings, 'STATSD_PREFIX', None))
