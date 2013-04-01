from django.conf import settings


def common(request):
    return {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
    }
