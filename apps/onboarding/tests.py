from django_webtest import WebTest
from django.core.urlresolvers import reverse
from django.core import mail

class OnboardingViewTest(WebTest):
    csrf_checks = False

    def test_sends_welcome_email(self):
        # Start adding a habit
        response = self.app.get(reverse('add_habit_step', args=['habit']))
        response.form.set('habit-description', 'Frobnicate my wibble')
        response.form.set('habit-target_value', '2')

        # Submit to reminders page
        response = response.form.submit()
        response = response.follow()

        # Submit to email entry page
        response = response.forms['skip-reminder-form'].submit()
        response = response.follow()
        response.form.set('summary-email', 'foo@bar.com')

        # Submit email entry form
        response = response.form.submit()
        response.follow()

        # Check welcome email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertTrue('welcome' in email.subject.lower())

