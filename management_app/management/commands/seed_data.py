import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from management_app.models import Accident, Alert, CongestionReport, Location, Profile

PLACES = [
    ('Bus Stand Chowk', 'Central', 31.6340, 74.8723), ('GT Road Crossing', 'North', 31.6500, 74.8800),
    ('Railway Station Road', 'Central', 31.6260, 74.8650), ('Mall Road Junction', 'West', 31.6410, 74.8590),
    ('Ring Road Flyover', 'East', 31.6120, 74.9100), ('Medical College Gate', 'South', 31.6010, 74.8700),
    ('Market Square', 'Central', 31.6330, 74.8770), ('Highway Toll Plaza', 'North', 31.6800, 74.8900),
    ('University Circle', 'West', 31.6450, 74.8300), ('Old City Gate', 'East', 31.6190, 74.8830),
]
TITLES = ['Two-wheeler skid', 'Car and truck collision', 'Rear-end collision', 'Pedestrian hit',
          'Bus and auto collision', 'Bike hit divider', 'Signal jumping crash', 'Wrong-side driving crash']


class Command(BaseCommand):
    help = 'Fill the database with demo users, locations, accidents, congestion reports and alerts.'

    def handle(self, *args, **options):
        random.seed(7)
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123', first_name='Admin')
        demo, created = User.objects.get_or_create(username='demo', defaults={
            'first_name': 'Demo', 'last_name': 'User', 'email': 'demo@example.com'})
        if created:
            demo.set_password('demo12345')
            demo.save()
        Profile.objects.get_or_create(user=demo, defaults={'phone': '9876543210', 'city': 'Amritsar'})
        admin = User.objects.get(username='admin')

        locs = [Location.objects.get_or_create(name=n, defaults={'zone': z, 'latitude': la, 'longitude': lo})[0]
                for n, z, la, lo in PLACES]
        if Accident.objects.exists():
            self.stdout.write('Data already present, skipping.')
            return
        now = timezone.now()
        weights = [5, 4, 3, 3, 2, 2, 3, 2, 1, 1]
        for _ in range(70):
            loc = random.choices(locs, weights)[0]
            sev = random.choices(['Minor', 'Major', 'Fatal'], [60, 32, 8])[0]
            Accident.objects.create(
                reporter=random.choice([demo, admin]), location=loc, title=random.choice(TITLES),
                description=f'Accident near {loc.name}. Traffic police informed and the lane was cleared after some time.',
                severity=sev, vehicles_involved=random.randint(1, 4),
                injuries=0 if sev == 'Minor' and random.random() < .6 else random.randint(1, 4),
                occurred_at=now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59)),
                status=random.choice(['Reported', 'Under Review', 'Resolved', 'Resolved']))
        causes = ['Peak Hours', 'Peak Hours', 'Accident', 'Road Work', 'Signal Failure', 'Weather', 'Event / Procession']
        for _ in range(180):
            loc = random.choices(locs, weights)[0]
            hour = random.choice([8, 9, 9, 10, 13, 17, 18, 18, 19, 20, 11, 15, 22, 6])
            peak = hour in (8, 9, 17, 18, 19)
            level = random.choices([1, 2, 3, 4], [1, 2, 4, 3] if peak else [5, 4, 2, 1])[0]
            when = (now - timedelta(days=random.randint(0, 29))).replace(hour=hour, minute=random.randint(0, 59))
            if when > now:
                when -= timedelta(days=1)
            CongestionReport.objects.create(
                reporter=random.choice([demo, admin]), location=loc, level=level,
                average_speed=max(5, int(random.gauss(55 - level * 11, 4))), cause=random.choice(causes),
                notes='', reported_at=when)
        Alert.objects.create(title='Heavy jam expected near Bus Stand Chowk', priority='Warning', location=locs[0],
                             message='Road work is going on. Please use the Mall Road route between 5 PM and 8 PM.', created_by=admin)
        Alert.objects.create(title='Signal not working at GT Road Crossing', priority='Critical', location=locs[1],
                             message='Traffic police are managing the junction manually. Drive slowly.', created_by=admin)
        Alert.objects.create(title='Fog advisory for morning hours', priority='Info',
                             message='Visibility is low before 8 AM. Use fog lights and keep a safe distance.', created_by=admin)
        self.stdout.write(self.style.SUCCESS('Demo data created. Admin: admin / admin123 | User: demo / demo12345'))
