from bs4 import BeautifulSoup
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
        response = response.forms['skip-reminder-form'].submit()
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

    def test_sends_welcome_email_with_functioning_confirm_link(self):
        self.test_sends_welcome_email()
        email = mail.outbox[0]
        self.assertEqual('text/html', email.alternatives[0][1])
        soup = BeautifulSoup(email.alternatives[0][0])
        confirm_url = soup.find('a')['href']

        # user should be inactive; when we hit the URL it should become active
        self.assertEqual(1, User.objects.filter(is_active=False, email='foo@bar.com').count())
        response = self.app.get(confirm_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, User.objects.filter(is_active=False, email='foo@bar.com').count())
        form = response.forms['confirm-email-form']
        response = form.submit()
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, User.objects.filter(is_active=True, email='foo@bar.com').count())
        # also our session (ie access via self.app) should be logged in
        # we test this by hitting the password change URL and seeing if we're
        # redirected (not logged in)
        response = self.app.get(reverse('password_change'))
        self.assertEqual(200, response.status_code)

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

    def test_data_is_preserved_between_steps(self):
        response = self.app.get(reverse('add_habit'))
        response = response.follow()

        form = response.forms['add-habit-form']
        form.set('habit-description', 'stop being an idiot')
        form.set('habit-target_value', '700')

        response = form.submit()
        response = response.follow()

        form = response.forms['reminder-form']
        form.set('reminder-trigger', 'being an idiot')
        form.set('reminder-days', True, index=0)
        form.set('reminder-email', 'whomever@example.com')

        response = form.submit()
        response = response.follow()

        form = response.forms['summary-form']
        email = form.fields['summary-email'][0].value

        self.assertEqual('whomever@example.com', email)

        response = response.forms['edit-habit-form'].submit()
        response = response.follow()

        form = response.forms['add-habit-form']
        self.assertEqual('stop being an idiot', form.fields['habit-description'][0].value)
