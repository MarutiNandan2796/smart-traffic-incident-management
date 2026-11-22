from .models import Alert


def traffic_global_context(request):
    """Provides active alerts to the navbar notification bell on every page."""
    try:
        active_alerts = list(Alert.objects.filter(is_active=True).select_related('location')[:5])
        active_count = Alert.objects.filter(is_active=True).count()
        return {
            'nav_active_alerts': active_alerts,
            'nav_active_alerts_count': active_count,
        }
    except Exception:
        return {
            'nav_active_alerts': [],
            'nav_active_alerts_count': 0,
        }
