from django.contrib import admin
from .models import Accident, Alert, CongestionReport, Location, Profile


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'latitude', 'longitude')
    list_filter = ('zone',)
    search_fields = ('name',)


@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'severity', 'status', 'occurred_at', 'reporter')
    list_filter = ('severity', 'status', 'location__zone')
    search_fields = ('title', 'description', 'location__name')
    date_hierarchy = 'occurred_at'


@admin.register(CongestionReport)
class CongestionAdmin(admin.ModelAdmin):
    list_display = ('location', 'level', 'average_speed', 'cause', 'reported_at')
    list_filter = ('level', 'cause')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'is_active', 'created_at')
    list_filter = ('priority', 'is_active')


admin.site.register(Profile)
