from django_webtest import WebTest
from django.core.urlresolvers import reverse
from django.core import mail

from apps.accounts.models import User


class OnboardingViewTest(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = User.objects.create_user(email='someone@example.com',
                                             password='123456')

    def test_sends_welcome_email(self):
        # Start adding a habit
        response = self.app.get(reverse('add_habit_step', args=['habit']))
        form = response.forms['add-habit-form']
        form.set('habit-description', 'Frobnicate my wibble')
        form.set('habit-target_value', '2')

        # Submit to reminders page
        response = form.submit()
        response = response.follow()

        # Submit to email entry page
        response = response.forms['skip-reminder'].submit()
        response = response.follow()

        # Submit email entry form
        form = response.forms['summary-form']
        form.set('summary-email', 'foo@bar.com')
        response = form.submit()
        response.follow()

        # Check welcome email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertTrue('welcome' in email.subject.lower())

    def test_add_habit_sends_email(self):
        self.user.is_active = True
        self.user.save()

        # Start adding a habit
        response = self.app.get(reverse('add_habit_step', args=['habit']),
                                user='someone@example.com')

        form = response.forms['add-habit-form']
        form.set('habit-description', 'Frobnicate my wibble')
        form.set('habit-target_value', '2')

        # Submit to reminders page
        response = form.submit()
        response = response.follow()

        # Submit to email entry page
        response = response.forms['skip-reminder-form'].submit()
        response = response.follow()

        # Submit email entry form
        response = response.forms['summary-form'].submit()
        response.follow()

        # Check welcome email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertTrue('new habit' in email.subject.lower())
