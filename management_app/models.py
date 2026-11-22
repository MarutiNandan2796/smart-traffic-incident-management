from django.conf import settings
from django.db import models
from django.utils import timezone


class Location(models.Model):
    """A road, junction or area of the city that we track."""
    ZONES = [
        ('North', 'North'), ('South', 'South'), ('East', 'East'),
        ('West', 'West'), ('Central', 'Central'),
    ]
    name = models.CharField(max_length=120, unique=True)
    zone = models.CharField(max_length=10, choices=ZONES, default='Central')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.zone})"


class Profile(models.Model):
    """Extra details for every user (phone and city)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Accident(models.Model):
    SEVERITY = [('Minor', 'Minor'), ('Major', 'Major'), ('Fatal', 'Fatal')]
    STATUS = [('Reported', 'Reported'), ('Under Review', 'Under Review'), ('Resolved', 'Resolved')]
    SEVERITY_POINTS = {'Minor': 1, 'Major': 3, 'Fatal': 5}

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accidents')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='accidents')
    title = models.CharField(max_length=150)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY, default='Minor')
    vehicles_involved = models.PositiveSmallIntegerField(default=1)
    injuries = models.PositiveSmallIntegerField(default=0)
    occurred_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=15, choices=STATUS, default='Reported')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self):
        return f"{self.title} - {self.location.name}"

    @property
    def points(self):
        return self.SEVERITY_POINTS.get(self.severity, 1)


class CongestionReport(models.Model):
    LEVELS = [(1, 'Low'), (2, 'Moderate'), (3, 'High'), (4, 'Severe')]
    CAUSES = [
        ('Peak Hours', 'Peak Hours'), ('Accident', 'Accident'), ('Road Work', 'Road Work'),
        ('Signal Failure', 'Signal Failure'), ('Weather', 'Weather'),
        ('Event / Procession', 'Event / Procession'), ('Other', 'Other'),
    ]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='congestion_reports')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='congestion_reports')
    level = models.PositiveSmallIntegerField(choices=LEVELS, default=2)
    average_speed = models.PositiveSmallIntegerField(help_text='Average vehicle speed in km/h', default=30)
    cause = models.CharField(max_length=30, choices=CAUSES, default='Peak Hours')
    notes = models.CharField(max_length=250, blank=True)
    reported_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.location.name} - {self.get_level_display()}"


class Alert(models.Model):
    PRIORITY = [('Info', 'Info'), ('Warning', 'Warning'), ('Critical', 'Critical')]
    title = models.CharField(max_length=120)
    message = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='Info')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
