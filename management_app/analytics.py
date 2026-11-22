"""Simple analysis helpers used by the dashboard, hotspot page and JSON API."""
from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from .models import Accident, CongestionReport, Location


def recent_window(days=30):
    return timezone.now() - timedelta(days=days)


def summary_counts(days=30):
    since = recent_window(days)
    accidents = Accident.objects.filter(occurred_at__gte=since)
    congestion = CongestionReport.objects.filter(reported_at__gte=since)
    return {
        'total_accidents': accidents.count(),
        'fatal': accidents.filter(severity='Fatal').count(),
        'injuries': accidents.aggregate(t=Sum('injuries'))['t'] or 0,
        'open_cases': Accident.objects.exclude(status='Resolved').count(),
        'avg_speed': round(congestion.aggregate(a=Avg('average_speed'))['a'] or 0, 1),
        'severe_reports': congestion.filter(level=4).count(),
    }


def accidents_by_severity(days=30):
    rows = Accident.objects.filter(occurred_at__gte=recent_window(days)).values('severity').annotate(c=Count('id'))
    data = {r['severity']: r['c'] for r in rows}
    return {k: data.get(k, 0) for k in ('Minor', 'Major', 'Fatal')}


def accidents_per_day(days=14):
    since = recent_window(days)
    counts = {}
    for a in Accident.objects.filter(occurred_at__gte=since):
        key = timezone.localtime(a.occurred_at).date()
        counts[key] = counts.get(key, 0) + 1
    labels, values = [], []
    for i in range(days - 1, -1, -1):
        d = (timezone.localtime() - timedelta(days=i)).date()
        labels.append(d.strftime('%d %b'))
        values.append(counts.get(d, 0))
    return {'labels': labels, 'values': values}


def congestion_by_hour(days=30):
    since = recent_window(days)
    totals = {h: [0, 0] for h in range(24)}
    for r in CongestionReport.objects.filter(reported_at__gte=since):
        h = timezone.localtime(r.reported_at).hour
        totals[h][0] += r.level
        totals[h][1] += 1
    labels = [f"{h:02d}:00" for h in range(24)]
    values = [round(t[0] / t[1], 2) if t[1] else 0 for t in totals.values()]
    return {'labels': labels, 'values': values}


def recommendation_for(row):
    """Turn numbers into a plain suggestion that a traffic officer can act on."""
    tips = []
    if row['fatal'] > 0:
        tips.append('Review junction design and install speed cameras')
    if row['accidents'] >= 4:
        tips.append('Add warning signs and street lights')
    if row['avg_level'] >= 3:
        tips.append('Re-time traffic signals and deploy police at peak hours')
    if row['avg_speed'] and row['avg_speed'] < 20:
        tips.append('Suggest alternate routes through alerts')
    if not tips:
        tips.append('Continue regular monitoring')
    return tips


def hotspots(days=30, limit=8):
    """Rank locations by a risk score = accident points + congestion points."""
    since = recent_window(days)
    rows = []
    for loc in Location.objects.all():
        acc = loc.accidents.filter(occurred_at__gte=since)
        cong = loc.congestion_reports.filter(reported_at__gte=since)
        acc_points = sum(a.points for a in acc)
        avg_level = cong.aggregate(a=Avg('level'))['a'] or 0
        avg_speed = cong.aggregate(a=Avg('average_speed'))['a'] or 0
        score = acc_points * 2 + round(avg_level * cong.count() * 0.5, 1)
        row = {
            'location': loc,
            'accidents': acc.count(),
            'fatal': acc.filter(severity='Fatal').count(),
            'avg_level': round(avg_level, 2),
            'avg_speed': round(avg_speed, 1),
            'score': round(score, 1),
        }
        row['tips'] = recommendation_for(row)
        if row['accidents'] or cong.exists():
            rows.append(row)
    rows.sort(key=lambda r: r['score'], reverse=True)
    return rows[:limit]
