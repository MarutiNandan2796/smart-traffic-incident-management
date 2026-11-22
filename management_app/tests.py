from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Accident, CongestionReport, Location
from . import analytics


class BaseCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ravi', 'ravi@example.com', 'pass12345')
        self.other = User.objects.create_user('sita', 'sita@example.com', 'pass12345')
        self.staff = User.objects.create_user('boss', 'boss@example.com', 'pass12345', is_staff=True)
        self.loc = Location.objects.create(name='Test Chowk', zone='Central', latitude=31.634, longitude=74.872)

    def make_accident(self, **kw):
        data = dict(reporter=self.user, location=self.loc, title='Test crash', description='x',
                    severity='Minor', occurred_at=timezone.now() - timedelta(hours=1))
        data.update(kw)
        return Accident.objects.create(**data)


class AuthTests(BaseCase):
    def test_pages_need_login(self):
        for name in ['dashboard', 'accident_list', 'congestion_list', 'hotspots', 'api_stats']:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302)

    def test_register_creates_user(self):
        r = self.client.post(reverse('register'), {
            'username': 'newuser', 'first_name': 'New', 'email': 'new@example.com',
            'password1': 'Str0ngPass!234', 'password2': 'Str0ngPass!234'})
        self.assertRedirects(r, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_login_and_report_accident(self):
        # 1. Register account
        r_reg = self.client.post(reverse('register'), {
            'username': 'marutinandan', 'first_name': 'Maruti', 'last_name': 'Nandan',
            'email': 'maruti@example.com', 'password1': 'ComplexPass123!@#', 'password2': 'ComplexPass123!@#'
        })
        self.assertRedirects(r_reg, reverse('dashboard'))
        user = User.objects.get(username='marutinandan')
        self.assertEqual(user.first_name, 'Maruti')

        # 2. Logout and login using registered credentials via login form
        self.client.logout()
        r_login = self.client.post(reverse('login'), {
            'username': 'marutinandan',
            'password': 'ComplexPass123!@#'
        })
        self.assertRedirects(r_login, reverse('dashboard'))

        # 3. Report an accident
        r_acc = self.client.post(reverse('accident_create'), {
            'title': 'Junction Overturn',
            'location': self.loc.pk,
            'severity': 'Minor',
            'vehicles_involved': 2,
            'injuries': 0,
            'description': 'Minor fender bender during evening peak hours.',
            'occurred_at': (timezone.localtime() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        })
        self.assertEqual(r_acc.status_code, 302)

        # 4. Check DB persistence and reporter assignment
        acc = Accident.objects.get(title='Junction Overturn')
        self.assertEqual(acc.reporter, user)

        # 5. Check 'mine' filter in accident registry
        r_list = self.client.get(reverse('accident_list') + '?mine=1')
        self.assertEqual(r_list.status_code, 200)
        self.assertIn(acc, r_list.context['page'].object_list)

        # 6. Check dashboard reflects report count
        r_dash = self.client.get(reverse('dashboard'))
        self.assertEqual(r_dash.status_code, 200)
        self.assertEqual(r_dash.context['my_reports'], 1)


class AccidentTests(BaseCase):
    def test_create_accident(self):
        self.client.login(username='ravi', password='pass12345')
        r = self.client.post(reverse('accident_create'), {
            'title': 'Bike skid', 'location': self.loc.pk, 'severity': 'Major', 'vehicles_involved': 1,
            'injuries': 1, 'description': 'Slipped on wet road',
            'occurred_at': (timezone.localtime() - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Accident.objects.count(), 1)

    def test_future_time_rejected(self):
        self.client.login(username='ravi', password='pass12345')
        r = self.client.post(reverse('accident_create'), {
            'title': 'x', 'location': self.loc.pk, 'severity': 'Minor', 'vehicles_involved': 1, 'injuries': 0,
            'description': 'x', 'occurred_at': (timezone.localtime() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Accident.objects.count(), 0)

    def test_only_owner_or_staff_can_delete(self):
        a = self.make_accident()
        self.client.login(username='sita', password='pass12345')
        self.client.post(reverse('accident_delete', args=[a.pk]))
        self.assertTrue(Accident.objects.filter(pk=a.pk).exists())
        self.client.login(username='ravi', password='pass12345')
        self.client.post(reverse('accident_delete', args=[a.pk]))
        self.assertFalse(Accident.objects.filter(pk=a.pk).exists())

    def test_search_filter(self):
        self.make_accident(title='Truck crash', severity='Fatal')
        self.make_accident(title='Small scratch')
        self.client.login(username='ravi', password='pass12345')
        r = self.client.get(reverse('accident_list'), {'severity': 'Fatal'})
        self.assertContains(r, 'Truck crash')
        self.assertNotContains(r, 'Small scratch')


class AnalyticsTests(BaseCase):
    def test_hotspot_score_and_tips(self):
        self.make_accident(severity='Fatal')
        rows = analytics.hotspots()
        self.assertEqual(rows[0]['score'], 10)  # fatal = 5 points, doubled
        self.assertIn('Review junction design and install speed cameras', rows[0]['tips'])

    def test_api_returns_json(self):
        self.make_accident()
        self.client.login(username='ravi', password='pass12345')
        data = self.client.get(reverse('api_stats')).json()
        self.assertEqual(data['summary']['total_accidents'], 1)


class AlertTests(BaseCase):
    def test_only_staff_can_publish_alert(self):
        self.client.login(username='ravi', password='pass12345')
        self.assertEqual(self.client.get(reverse('alert_create')).status_code, 302)
        self.client.login(username='boss', password='pass12345')
        self.assertEqual(self.client.get(reverse('alert_create')).status_code, 200)


class ExportAndInteractiveFeatureTests(BaseCase):
    def test_export_accidents_csv(self):
        self.make_accident(title='Expressway Pileup')
        self.client.login(username='ravi', password='pass12345')
        r = self.client.get(reverse('export_accidents_csv'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv; charset=utf-8')
        content = r.content.decode('utf-8')
        self.assertIn('Expressway Pileup', content)
        self.assertIn('Test Chowk', content)

    def test_export_congestion_csv(self):
        CongestionReport.objects.create(
            reporter=self.user, location=self.loc, level=3,
            average_speed=22, cause='Road Work', reported_at=timezone.now()
        )
        self.client.login(username='ravi', password='pass12345')
        r = self.client.get(reverse('export_congestion_csv'))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf-8')
        self.assertIn('Road Work', content)

    def test_export_hotspots_csv(self):
        self.make_accident(severity='Fatal')
        self.client.login(username='ravi', password='pass12345')
        r = self.client.get(reverse('export_hotspots_csv'))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf-8')
        self.assertIn('Test Chowk', content)

    def test_api_map_data(self):
        self.make_accident()
        self.client.login(username='ravi', password='pass12345')
        r = self.client.get(reverse('api_map_data'))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('locations', data)
        self.assertEqual(len(data['locations']), 1)
        self.assertEqual(data['locations'][0]['name'], 'Test Chowk')

    def test_staff_can_update_accident_status(self):
        acc = self.make_accident(status='Reported')
        self.client.login(username='boss', password='pass12345')
        r = self.client.post(reverse('accident_status_update', args=[acc.pk]), {'status': 'Resolved'})
        self.assertRedirects(r, reverse('accident_detail', args=[acc.pk]))
        acc.refresh_from_db()
        self.assertEqual(acc.status, 'Resolved')

    def test_non_staff_cannot_update_accident_status(self):
        acc = self.make_accident(status='Reported')
        self.client.login(username='ravi', password='pass12345')
        r = self.client.post(reverse('accident_status_update', args=[acc.pk]), {'status': 'Resolved'})
        self.assertRedirects(r, reverse('accident_detail', args=[acc.pk]))
        acc.refresh_from_db()
        self.assertEqual(acc.status, 'Reported')
