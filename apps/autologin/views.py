"""
Auto login links from email. Note that the default token generator
is designed for password resets, where last_login & the password
salt would both change. However we use this only where the user
isn't logged in, meaning that we'll run login() during processing,
and last_login will change. So this is a one-shot token, although
then you'll be logged in using the correct user and can keep on using
the same link until you log out again. Attempts to use this
while logged in as another user will just fail.

When we pass through as logged in, we also update last_login on
the user so that the same token now won't work unless you're already
logged in as that user. This provides some protection against people
forwarding an email to an attacker thus allowing them to log in as
the original user.
"""

from urllib import urlencode
from django.contrib.auth import login, get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, int_to_base36
from django.utils.crypto import salted_hmac
from django.utils import six
from django.views.decorators.cache import never_cache


class FlexibleTokenGenerator(PasswordResetTokenGenerator):
    key_salt = None

    def _make_token_with_timestamp(self, user, timestamp):
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)

        # By hashing on the internal state of the user and using state
        # that is sure to change, we produce a hash that will be
        # invalid as soon as it is used.
        # We limit the hash to 20 chars to keep URL short

        # Ensure results are consistent across DB backends
        login_timestamp = user.last_login.replace(microsecond=0, tzinfo=None)

        value = (six.text_type(user.pk) + user.password +
                six.text_type(login_timestamp) + six.text_type(timestamp))
        hash = salted_hmac(self.key_salt, value).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)


class AutoLoginTokenGenerator(FlexibleTokenGenerator):
    key_salt = "apps.autologin.AutoLoginTokenGenerator"


default_token_generator = AutoLoginTokenGenerator()

@never_cache
def auto_login(request, uidb36, token, template="autologin/failed.html", redirect_to="/"):
    redirect = request.GET.get('next', None)
    args = request.GET.copy()
    if 'next' in args:
        del args['next']
    args = args.urlencode()
    if redirect is None:
        redirect = redirect_to
    if args != "":
        if '?' in redirect:
            redirect += '&'
        else:
            redirect += '?'
        redirect += args
    User = get_user_model()
    try:
        user = User.objects.get(pk=base36_to_int(uidb36))
    except (ValueError, User.DoesNotExist):
        user = None

    if request.user.is_authenticated():
        if request.user == user:
            update_last_login(None, user)
            return HttpResponseRedirect(redirect)
        else:
            user = None

    if user is None or not default_token_generator.check_token(user, token):
        return TemplateResponse(request, template, {}, status=400)
    else:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return HttpResponseRedirect(redirect)


def make_auto_login_link(user, redirect=None):
    if redirect is None:
        query = ''
    else:
        query = '?' + urlencode(dict(next=redirect))
    return reverse(
        'apps.autologin.views.auto_login',
        kwargs = {
            'uidb36': int_to_base36(user.pk),
            'token': default_token_generator.make_token(user),
            },
        ) + query
