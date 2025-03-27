from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ecopoints.models import Category, Task, CompletedTask
from django.utils import timezone

class InsightsViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@test.com',
            password='12345',
        )
        self.client.login(username='testuser', password='12345')

        self.category = Category.objects.create(name='Recycling')
        self.category.likes = 0
        self.category.save()

        self.task = Task.objects.create(name='Recycle Bottle', category=self.category, score=10, description="Test task")

        # Simulate tasks completed s on different days
        now = timezone.now()
        CompletedTask.objects.create(user=self.user, task=self.task, completed_at=now)
        CompletedTask.objects.create(user=self.user, task=self.task, completed_at=now - timezone.timedelta(days=1))
        CompletedTask.objects.create(user=self.user, task=self.task, completed_at=now - timezone.timedelta(days=2))


    def test_insights_view_authenticated(self):
        self.client.login(username='testuser', password='12345')

        # Access Insights page
        response = self.client.get(reverse('ecopoints:insights'))

        self.assertEqual(response.status_code, 200)

        self.assertIn('daily_points', response.context)
        self.assertIn('weekly_data', response.context)
        self.assertIn('bubble_chart_data', response.context)
        self.assertIn('bar_chart_data', response.context)

        self.assertGreaterEqual(response.context['daily_points'], 10)


    def test_insights_view_redirect_if_not_logged_in(self):
        self.client.logout()

        response = self.client.get(reverse('ecopoints:insights'))

        self.assertRedirects(response, '/accounts/login/?next=/ecopoints/insights/')


    def test_bubble_chart_data_structure(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('ecopoints:insights'))

        self.assertEqual(response.status_code, 200)
        bubble_data = response.context['bubble_chart_data']

        self.assertIsInstance(bubble_data, list)
        self.assertTrue(len(bubble_data) > 0)

        sample = bubble_data[0]
        self.assertIn('day', sample)
        self.assertIn('task__category__name', sample)
        self.assertIn('points', sample)


    def test_stacked_bar_data_structure(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('ecopoints:insights'))

        self.assertEqual(response.status_code, 200)
        bar_data = response.context['bar_chart_data']

        self.assertIsInstance(bar_data, list)
        self.assertTrue(len(bar_data) > 0)

        sample = bar_data[0]
        self.assertIn('month', sample)
        self.assertIn('task__category__name', sample)
        self.assertIn('points', sample)


    def test_donut_chart_data(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('ecopoints:insights'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('daily_points', response.context)

        daily_points = response.context['daily_points']
        self.assertIsInstance(daily_points, int)
        self.assertGreaterEqual(daily_points, 10)


    def test_weekly_chart_data(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('ecopoints:insights'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('weekly_data', response.context)

        weekly_data = response.context['weekly_data']
        self.assertIsInstance(weekly_data, list)
        self.assertGreater(len(weekly_data), 0)

        sample = weekly_data[0]
        self.assertIn('day', sample)
        self.assertIn('points', sample)
        self.assertIsInstance(sample['day'], int)
        self.assertIsInstance(sample['points'], int)


    def test_monthly_recap_data(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('ecopoints:insights'))

        self.assertEqual(response.status_code, 200)

        self.assertIn('monthly_points', response.context)
        self.assertIn('days_with_tasks', response.context)
        self.assertIn('total_completed_tasks', response.context)

        self.assertIsInstance(response.context['monthly_points'], int)
        self.assertIsInstance(response.context['days_with_tasks'], int)
        self.assertIsInstance(response.context['total_completed_tasks'], int)

        self.assertEqual(response.context['days_with_tasks'], 3)
        self.assertEqual(response.context['total_completed_tasks'], 3)
        self.assertEqual(response.context['monthly_points'], 30)

