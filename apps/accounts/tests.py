from django_webtest import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from apps.accounts.models import User


class PasswordChangeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='someone@example.com',
                                             password='12345',
                                             is_active=True)
        self.client.login(email=self.user.email, password='12345')

    def test_successful_password_change(self):
        response = self.client.post(reverse('password_change'), {
            'old_password': '12345',
            'new_password1': '54321',
            'new_password2': '54321',
        })
        self.assertRedirects(response, reverse('password_change_done'))

        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        self.assertEqual('Your password has been changed', email.subject)

    def test_failing_password_change(self):
        response = self.client.post(reverse('password_change'))
        self.assertEqual(0, len(mail.outbox))

    def test_change_password_form(self):
        response = self.client.get(reverse('password_change'))
        self.assertEqual(0, len(mail.outbox))
