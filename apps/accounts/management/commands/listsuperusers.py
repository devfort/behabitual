from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        User = get_user_model()
        for u in User.objects.filter(is_superuser=True):
            print u.email

