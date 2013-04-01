# Django settings for hobbit project.
from os import environ as env
import os.path
import sys

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

DEBUG = 'true' == env.get('DJANGO_DEBUG', 'true')
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

CONTACT_EMAIL = 'help@behabitual.com'

if 'true' == env.get('EMAIL_DEBUG', 'false'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    if 'true' == env.get('EMAIL_LIVE', 'false'):
        EMAIL_HOST = env.get('EMAIL_HOST')
        EMAIL_HOST_USER = env.get('EMAIL_USER')
        EMAIL_HOST_PASSWORD = env.get('EMAIL_HOST_PASSWORD')
        EMAIL_PORT = env.get('EMAIL_PORT')
        EMAIL_USE_TLS = 'true' == env.get('EMAIL_USE_TLS', 'true')
        DEFAULT_FROM_EMAIL  = env.get('DEFAULT_FROM_EMAIL', CONTACT_EMAIL)
    else:
        EMAIL_HOST          = env.get('EMAIL_HOST', 'localhost')
        EMAIL_PORT          = env.get('EMAIL_PORT', '25')
        EMAIL_HOST_USER     = env.get('EMAIL_USER', 'vagrant')
        EMAIL_HOST_PASSWORD = env.get('EMAIL_HOST_PASSWORD', 'vagrant')
        EMAIL_USE_TLS       = env.get('EMAIL_USE_TLS', 'true') == 'true'
        DEFAULT_FROM_EMAIL  = env.get('DEFAULT_FROM_EMAIL', 'hobbit@dev.fort')
        DEFAULT_TO_EMAIL    = ('vagrant@dev.fort',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hobbit',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}
# Pick up Heroku's database, if that's where we're running.
try:
    import dj_database_url
    database = dj_database_url.config()
    if database:
        DATABASES['default'] = database
except ImportError:
    pass

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-gb'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

if 'AWS_ACCESS_KEY_ID' in env:
    # AWS is available, so use this for media storage *and* as a target for
    # static assets in the staticfiles pipeline.
    AWS_ACCESS_KEY_ID = env['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = env['AWS_SECRET_ACCESS_KEY']
    AWS_AVAILABLE = True
else:
    AWS_AVAILABLE = False

if AWS_AVAILABLE and 'AWS_STORAGE_BUCKET_NAME' in env:
    AWS_STORAGE_BUCKET_NAME = env['AWS_STORAGE_BUCKET_NAME']
    AWS_QUERYSTRING_AUTH = False
    AWS_HEADERS = {
        'Cache-Control': 'max-age=86400',
    }

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    MEDIA_URL = "https://%s.s3.amazonaws.com/" % env['AWS_STORAGE_BUCKET_NAME']
    MEDIA_ROOT = ''

    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    # The next two aren't really used, but staticfiles will complain without them
    STATIC_URL = "https://%s.s3.amazonaws.com/" % env['AWS_STORAGE_BUCKET_NAME']
    STATIC_ROOT = ''
else:
    MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')
    MEDIA_URL = '/media/'
    STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
    STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'assets'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# The default is for development only; we set this via the environment for deployment
if DEBUG:
    SECRET_KEY = '#u)ftxq%-e6_e+&jeff$=he2miu(=51k2!mcj3fffkso9rd*&8*'
else:
    SECRET_KEY = env.get('DJANGO_SECRET_KEY')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "hobbit.context_processors.common",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'hobbit.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'hobbit.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(SITE_ROOT, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'gunicorn',
    'south',
    'apps.accounts',
    'apps.encouragements',
    'apps.habits',
    'apps.onboarding',
    'apps.homepage',
)

AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'homepage'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Configure the global Statsd host

# STATSD_HOST = 'localhost'
# STATSD_PORT = 8125
# STATSD_PREFIX = ''

if 'true' == env.get('FULLY_SECURE'):
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000 # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") # Heroku sends this

ALLOWED_HOSTS = env.get('ALLOWED_HOSTS', 'localhost').split(';')

if not DEBUG:
    PREPEND_WWW = True

GOOGLE_ANALYTICS_ID = env.get('GOOGLE_ANALYTICS_ID', 'UA-39256165-2')
