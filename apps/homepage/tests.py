from django_webtest import TestCase
from django.core.urlresolvers import reverse

import datetime

from apps.accounts.models import User
from apps.habits.models import Habit


class HomepageTest(TestCase):
    def setUp(self):
        self.user_password = '12345'
        self.user = User.objects.create_user(
            email='someone@example.com', password=self.user_password
        )

    # TODO: Logged out homepage
    def test_logged_out_homepage(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed("homepage/home.html")

    def test_logged_in_homepage_is_dashboard(self):
        self.client.login(
            email=self.user.email, password=self.user_password
        )
        response = self.client.get(reverse('homepage'))
        self.assertTemplateUsed("homepage/user_dashboard.html")

    def test_dashboard_contains_habit(self):
        self.client.login(
            email=self.user.email, password=self.user_password
        )
        habit = Habit.objects.create(
            description="Brush my teeth",
            start=datetime.date.today(),
            user=self.user,
            resolution='day'
        )
        response = self.client.get(reverse('homepage'))
        self.assertContains(response, habit.description, 1)
