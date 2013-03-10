import datetime
from django_webtest import TestCase, WebTest
from django.core.urlresolvers import reverse
from django.core import mail

from apps.accounts.models import User
from apps.habits.models import Habit


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


class SettingsTest(WebTest):
    def setUp(self):
        self.user = User.objects.create_user(email='someone@example.com',
                                             password='12345',
                                             is_active=True)

    def test_disabling_data_collection_email(self):
        habit1 = Habit.objects.create(
            user=self.user,
            description='brush teeth',
            start=datetime.date.today(),
        )
        habit2 = Habit.objects.create(
            user=self.user,
            description='drink lots',
            start=datetime.date.today(),
        )

        response = self.app.get(
            reverse('account_settings'),
            user='someone@example.com',
        )

        form = response.forms['settings-form']
        form.set('form-0-send_data_collection_emails', False)
        response = form.submit()

        self.assertEqual(302, response.status_code)

        habit1 = Habit.objects.get(pk=habit1.pk)
        self.assertTrue(habit1.send_data_collection_emails)

        habit2 = Habit.objects.get(pk=habit2.pk)
        self.assertFalse(habit2.send_data_collection_emails)

    def test_enabling_data_collection_email(self):
        habit1 = Habit.objects.create(
            user=self.user,
            description='brush teeth',
            start=datetime.date.today(),
            send_data_collection_emails=False,
        )
        habit2 = Habit.objects.create(
            user=self.user,
            description='drink lots',
            start=datetime.date.today(),
            send_data_collection_emails=False,
        )

        response = self.app.get(
            reverse('account_settings'),
            user='someone@example.com',
        )

        form = response.forms['settings-form']
        form.set('form-0-send_data_collection_emails', True)
        response = form.submit()

        self.assertEqual(302, response.status_code)

        habit1 = Habit.objects.get(pk=habit1.pk)
        self.assertFalse(habit1.send_data_collection_emails)

        habit2 = Habit.objects.get(pk=habit2.pk)
        self.assertTrue(habit2.send_data_collection_emails)
