import datetime

from django.test import TestCase
from django_webtest import WebTest
from django.core.urlresolvers import reverse

from apps.accounts.models import User
from apps.habits.models import Habit, TimePeriod


class HabitArchiveViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='someone@example.com', password='123456', is_active=True
        )
        self.client.login(email='someone@example.com', password='123456')
        self.habit = Habit.objects.create(
            description="Brush my teeth",
            start=datetime.date.today(),
            user=self.user,
            resolution='day'
        )

    def test_archive_habit(self):
        response = self.client.post(reverse('habit_archive', args=[self.habit.id]), {
            'archive': '1'
        }, HTTP_REFERER=reverse('homepage'))
        self.assertRedirects(response, reverse('homepage'))

        self.habit = Habit.objects.get(pk=self.habit.pk)

        self.assertEquals(True, self.habit.archived)

    def test_unarchive_habit(self):
        self.habit.archived = True
        self.habit.save()
        response = self.client.post(reverse('habit_archive', args=[self.habit.id]), {
            'archive': '0'
        })
        self.assertRedirects(response, reverse('habit', args=[self.habit.id]))

        self.habit = Habit.objects.get(pk=self.habit.pk)

        self.assertEquals(False, self.habit.archived)


class HabitRecordViewTest(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = User.objects.create_user(
            email='someone@example.com', password='123456'
        )
        self.habit = Habit.objects.create(
            description="Brush my teeth",
            start=datetime.date.today(),
            user=self.user,
            resolution='day',
            target_value=2,
        )

    def test_record_get(self):
        # Simple test to make sure the record view shows without error
        self.habit.record(self.habit.get_time_period(self.habit.start), 2)
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        self.assertRedirects(response, reverse('homepage'))

    def test_record_get_no_data_needed(self):
        # Simple test to make sure the record view shows without error
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')

    def test_record_post(self):
        time_period = self.habit.get_current_time_period()
        params = {
            '0-date': time_period.date,
            '0-value': 2,
        }
        response = self.app.post(reverse('habit_record', args=[self.habit.id]), params, user='someone@example.com')
        self.assertRedirects(response, reverse('habit_encouragement', args=[self.habit.id]))

        bucket = self.habit.get_buckets().get(index=time_period.index)
        self.assertEquals(2, bucket.value)

    def test_record_post_two(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=1),
            user=self.user,
            resolution='day',
            target_value=2,
        )
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        form = form = response.forms['data-entry']
        form.set('0-value', 1)
        form.set('1-value', 2)
        resp = form.submit()
        self.assertEqual(302, resp.status_code)
        self.assertEqual('http://localhost:80' + reverse('habit_encouragement', args=[self.habit.id]), resp.headers['Location'])

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(1, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(2, bucket.value)

    def test_record_post_two_not_at_start(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=2),
            user=self.user,
            resolution='day',
            target_value=2,
        )
        self.habit.record(self.habit.get_time_period(self.habit.start), 17)
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        form = response.forms['data-entry']
        with self.assertRaises(AssertionError):
            # not in the form because data already exists
            form.set('0-value', 1000)
        form.set('1-value', 41)
        form.set('2-value', 108)
        resp = form.submit()
        self.assertEqual(302, resp.status_code)
        self.assertEqual('http://localhost:80' + reverse('habit_encouragement', args=[self.habit.id]), resp.headers['Location'])

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(17, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(41, bucket.value)
        bucket = self.habit.get_buckets().get(index=2)
        self.assertEquals(108, bucket.value)

    def test_record_post_ignore_existing_buckets(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=1),
            user=self.user,
            resolution='day',
            target_value=2,
        )
        self.habit.record(self.habit.get_time_period(self.habit.start), 17)
        time_period = self.habit.get_current_time_period()
        params = {
            '0-date': time_period.date,
            '0-value': 2,
            '1-date': time_period.date,
            '1-value': 2,
        }
        response = self.app.post(reverse('habit_record', args=[self.habit.id]), params, user='someone@example.com')
        self.assertRedirects(response, reverse('habit_encouragement', args=[self.habit.id]))

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(17, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(2, bucket.value)

    def test_post_leading_gap(self):
        time_period = self.habit.get_current_time_period()
        params = {
            '0-date': time_period.date,
            '0-value': ' 2',
        }
        response = self.app.post(reverse('habit_record', args=[self.habit.id]), params, user='someone@example.com')
        self.assertRedirects(response, reverse('habit_encouragement', args=[self.habit.id]))

        bucket = self.habit.get_buckets().get(index=time_period.index)
        self.assertEquals(2, bucket.value)

    def test_post_yes_no_habit(self):
        self.habit = Habit.objects.create(
            description="Frob my Hobbits",
            start=datetime.date.today() - datetime.timedelta(days=2),
            user=self.user,
            resolution='day',
            target_value=1,
        )
        self.habit.record(self.habit.get_time_period(self.habit.start), 1)
        response = self.app.get(reverse('habit_record', args=[self.habit.id]), user='someone@example.com')
        form = response.forms['data-entry']
        with self.assertRaises(AssertionError):
            # not in the form because data already exists
            form.set('0-value', 1000)

        # Index=1 says submit the second (0-based). 0: hidden, 1: checkbox
        form.set('1-value', 0, index=1)
        form.set('2-value', 1, index=1)
        resp = form.submit()
        self.assertEqual(302, resp.status_code)
        self.assertEqual('http://localhost:80' + reverse('habit_encouragement', args=[self.habit.id]), resp.headers['Location'])

        bucket = self.habit.get_buckets().get(index=0)
        self.assertEquals(1, bucket.value)
        bucket = self.habit.get_buckets().get(index=1)
        self.assertEquals(0, bucket.value)
        bucket = self.habit.get_buckets().get(index=2)
        self.assertEquals(1, bucket.value)
