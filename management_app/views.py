import csv
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import analytics, gemini_service
from .forms import (AccidentForm, AlertForm, CongestionForm, ProfileForm,
                    RegisterForm, UserUpdateForm)
from .models import Accident, Alert, CongestionReport, Location, Profile

staff_required = user_passes_test(lambda u: u.is_staff, login_url='login')


def home(request):
    counts = analytics.summary_counts()
    active_alerts = Alert.objects.filter(is_active=True).select_related('location')[:5]
    latest_accidents = Accident.objects.select_related('location', 'reporter')[:6]
    locations = Location.objects.all()
    hotspots_preview = analytics.hotspots(limit=4)
    
    context = {
        'alerts': active_alerts,
        'counts': counts,
        'latest': latest_accidents,
        'locations': locations,
        'hotspots': hotspots_preview,
    }
    return render(request, 'management_app/home.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        Profile.objects.get_or_create(user=user)
        login(request, user)
        messages.success(request, f'Welcome aboard, {user.first_name or user.username}! Your account is ready.')
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    days = int(request.GET.get('days', 30))
    if days not in (7, 14, 30, 60):
        days = 30
    counts = analytics.summary_counts(days=days)
    my_reports = Accident.objects.filter(reporter=request.user).count()
    active_alerts = Alert.objects.filter(is_active=True).select_related('location')[:4]
    hotspot_list = analytics.hotspots(days=days, limit=4)
    locations = Location.objects.all()
    
    context = {
        'counts': counts,
        'my_reports': my_reports,
        'alerts': active_alerts,
        'hotspots': hotspot_list,
        'locations': locations,
        'selected_days': days,
    }
    return render(request, 'management_app/dashboard.html', context)


def _filter_accidents(request):
    qs = Accident.objects.select_related('location', 'reporter')
    q = request.GET.get('q', '').strip()
    severity = request.GET.get('severity', '')
    status = request.GET.get('status', '')
    location = request.GET.get('location', '')
    zone = request.GET.get('zone', '')
    mine = request.GET.get('mine', '')
    
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(location__name__icontains=q) |
            Q(reporter__username__icontains=q) |
            Q(reporter__first_name__icontains=q) |
            Q(reporter__last_name__icontains=q)
        )
    if severity:
        qs = qs.filter(severity=severity)
    if status:
        qs = qs.filter(status=status)
    if location:
        qs = qs.filter(location_id=location)
    if zone:
        qs = qs.filter(location__zone=zone)
    if mine == '1' and request.user.is_authenticated:
        qs = qs.filter(reporter=request.user)
    return qs


@login_required
def accident_list(request):
    qs = _filter_accidents(request)
    
    # Summary stats for filter KPI chips
    all_qs = Accident.objects.all()
    my_count = all_qs.filter(reporter=request.user).count() if request.user.is_authenticated else 0
    stats = {
        'total': all_qs.count(),
        'open': all_qs.filter(status='Reported').count(),
        'review': all_qs.filter(status='Under Review').count(),
        'resolved': all_qs.filter(status='Resolved').count(),
        'fatal': all_qs.filter(severity='Fatal').count(),
        'mine': my_count,
    }
    
    page = Paginator(qs, 8).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    
    context = {
        'page': page,
        'locations': Location.objects.all(),
        'severities': Accident.SEVERITY,
        'statuses': Accident.STATUS,
        'zones': Location.ZONES,
        'querystring': params.urlencode(),
        'total': qs.count(),
        'stats': stats,
        'selected_zone': request.GET.get('zone', ''),
        'selected_mine': request.GET.get('mine', ''),
    }
    return render(request, 'management_app/accident_list.html', context)


@login_required
def accident_create(request):
    form = AccidentForm(request.POST or None, is_staff=request.user.is_staff)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.reporter = request.user
        obj.save()
        messages.success(request, f'Accident report #{obj.pk} registered successfully.')
        return redirect('accident_detail', pk=obj.pk)
    return render(request, 'management_app/form_page.html', {
        'form': form,
        'heading': 'Report Traffic Incident',
        'subheading': 'Submit verified road accident details to trigger emergency response and hazard mapping.',
        'btn_text': 'Submit Incident Report'
    })


@login_required
def accident_detail(request, pk):
    obj = get_object_or_404(Accident.objects.select_related('location', 'reporter'), pk=pk)
    can_edit = request.user.is_staff or obj.reporter_id == request.user.id
    can_change_status = request.user.is_staff
    recent_nearby = Accident.objects.filter(location=obj.location).exclude(pk=obj.pk)[:3]
    active_alerts = Alert.objects.filter(location=obj.location, is_active=True)[:2]
    
    return render(request, 'management_app/accident_detail.html', {
        'obj': obj,
        'can_edit': can_edit,
        'can_change_status': can_change_status,
        'statuses': Accident.STATUS,
        'recent_nearby': recent_nearby,
        'active_alerts': active_alerts,
    })


@login_required
def accident_update(request, pk):
    obj = get_object_or_404(Accident, pk=pk)
    if not (request.user.is_staff or obj.reporter_id == request.user.id):
        messages.error(request, 'You can only edit your own reports.')
        return redirect('accident_detail', pk=pk)
    form = AccidentForm(request.POST or None, instance=obj, is_staff=request.user.is_staff)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Incident report #{pk} has been updated.')
        return redirect('accident_detail', pk=pk)
    return render(request, 'management_app/form_page.html', {
        'form': form,
        'heading': f'Edit Incident Report #{pk}',
        'subheading': 'Update incident description, vehicle count, severity, or location details.',
        'btn_text': 'Save Changes'
    })


@login_required
@require_POST
def accident_status_update(request, pk):
    obj = get_object_or_404(Accident, pk=pk)
    if not request.user.is_staff:
        messages.error(request, 'Only authorized traffic officers can change report status.')
        return redirect('accident_detail', pk=pk)
    
    new_status = request.POST.get('status')
    valid_statuses = dict(Accident.STATUS)
    if new_status in valid_statuses:
        obj.status = new_status
        obj.save(update_fields=['status'])
        messages.success(request, f'Status updated to "{new_status}".')
    else:
        messages.error(request, 'Invalid status specified.')
    return redirect('accident_detail', pk=pk)


@login_required
@require_POST
def accident_delete(request, pk):
    obj = get_object_or_404(Accident, pk=pk)
    if request.user.is_staff or obj.reporter_id == request.user.id:
        title = obj.title
        obj.delete()
        messages.success(request, f'Report "{title}" was permanently removed.')
    else:
        messages.error(request, 'You are not allowed to delete this report.')
    return redirect('accident_list')


@login_required
def export_accidents_csv(request):
    """Exports accident dataset to CSV with active filters applied."""
    qs = _filter_accidents(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="trafficsafe_accidents_report.csv"'
    
    # Write UTF-8 BOM so Excel opens Hindi / special characters accurately
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Location', 'Zone', 'Severity', 'Status',
        'Vehicles Involved', 'Injuries Reported', 'Occurred At (IST)',
        'Reported By', 'Description'
    ])
    for a in qs:
        writer.writerow([
            a.id,
            a.title,
            a.location.name,
            a.location.zone,
            a.severity,
            a.status,
            a.vehicles_involved,
            a.injuries,
            timezone.localtime(a.occurred_at).strftime('%Y-%m-%d %H:%M'),
            a.reporter.get_full_name() or a.reporter.username,
            a.description.replace('\n', ' ')
        ])
    return response


def _filter_congestion(request):
    qs = CongestionReport.objects.select_related('location', 'reporter')
    level = request.GET.get('level', '')
    location = request.GET.get('location', '')
    zone = request.GET.get('zone', '')
    if level:
        qs = qs.filter(level=level)
    if location:
        qs = qs.filter(location_id=location)
    if zone:
        qs = qs.filter(location__zone=zone)
    return qs


@login_required
def congestion_list(request):
    qs = _filter_congestion(request)
    avg_speed = qs.aggregate(a=Avg('average_speed'))['a'] or 0
    severe_count = qs.filter(level=4).count()
    
    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    
    return render(request, 'management_app/congestion_list.html', {
        'page': page,
        'levels': CongestionReport.LEVELS,
        'locations': Location.objects.all(),
        'zones': Location.ZONES,
        'querystring': params.urlencode(),
        'avg_speed': round(avg_speed, 1),
        'severe_count': severe_count,
        'total': qs.count(),
        'selected_zone': request.GET.get('zone', ''),
    })


@login_required
def congestion_create(request):
    form = CongestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.reporter = request.user
        obj.save()
        messages.success(request, f'Congestion report for {obj.location.name} recorded.')
        return redirect('congestion_list')
    return render(request, 'management_app/form_page.html', {
        'form': form,
        'heading': 'Report Traffic Congestion',
        'subheading': 'Broadcast real-time slowdowns, blockages, or traffic density.',
        'btn_text': 'Submit Traffic Report'
    })


@login_required
@require_POST
def congestion_delete(request, pk):
    obj = get_object_or_404(CongestionReport, pk=pk)
    if request.user.is_staff or obj.reporter_id == request.user.id:
        obj.delete()
        messages.success(request, 'Congestion report deleted.')
    else:
        messages.error(request, 'You are not allowed to delete this report.')
    return redirect('congestion_list')


@login_required
def export_congestion_csv(request):
    qs = _filter_congestion(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="trafficsafe_congestion_report.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Location', 'Zone', 'Level ID', 'Level Name',
        'Average Speed (km/h)', 'Primary Cause', 'Reported At (IST)', 'Notes', 'Reporter'
    ])
    for c in qs:
        writer.writerow([
            c.id,
            c.location.name,
            c.location.zone,
            c.level,
            c.get_level_display(),
            c.average_speed,
            c.cause,
            timezone.localtime(c.reported_at).strftime('%Y-%m-%d %H:%M'),
            c.notes,
            c.reporter.username
        ])
    return response


@login_required
def alert_list(request):
    qs = Alert.objects.select_related('location', 'created_by')
    priority = request.GET.get('priority', '')
    status = request.GET.get('status', '')
    
    if priority:
        qs = qs.filter(priority=priority)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'closed':
        qs = qs.filter(is_active=False)
        
    counts = {
        'total': Alert.objects.count(),
        'active': Alert.objects.filter(is_active=True).count(),
        'critical': Alert.objects.filter(is_active=True, priority='Critical').count(),
        'warning': Alert.objects.filter(is_active=True, priority='Warning').count(),
        'info': Alert.objects.filter(is_active=True, priority='Info').count(),
    }
    
    return render(request, 'management_app/alert_list.html', {
        'alerts': qs,
        'counts': counts,
        'priorities': Alert.PRIORITY,
        'selected_priority': priority,
        'selected_status': status,
    })


@staff_required
def alert_create(request):
    form = AlertForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, f'Public Alert "{obj.title}" broadcasted.')
        return redirect('alert_list')
    return render(request, 'management_app/form_page.html', {
        'form': form,
        'heading': 'Publish Official Traffic Alert',
        'subheading': 'Broadcast emergency road advisories, hazard warnings, or diversions to citizens.',
        'btn_text': 'Publish Alert Now'
    })


@staff_required
@require_POST
def alert_toggle(request, pk):
    obj = get_object_or_404(Alert, pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    state = 're-opened' if obj.is_active else 'closed'
    messages.success(request, f'Alert "{obj.title}" marked as {state}.')
    return redirect('alert_list')


@login_required
def hotspot_view(request):
    zone = request.GET.get('zone', '')
    rows = analytics.hotspots(limit=20)
    if zone:
        rows = [r for r in rows if r['location'].zone == zone]
        
    stats = {
        'total_hotspots': len(rows),
        'high_risk': len([r for r in rows if r['score'] >= 15]),
        'critical_fatals': sum(r['fatal'] for r in rows),
    }
    
    return render(request, 'management_app/hotspots.html', {
        'rows': rows,
        'zones': Location.ZONES,
        'selected_zone': zone,
        'stats': stats,
    })


@login_required
def export_hotspots_csv(request):
    rows = analytics.hotspots(limit=50)
    zone = request.GET.get('zone', '')
    if zone:
        rows = [r for r in rows if r['location'].zone == zone]
        
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="trafficsafe_hotspots_action_plan.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'Rank', 'Location Name', 'Zone', 'Accidents (30d)', 'Fatal Incidents',
        'Average Congestion Level', 'Average Speed (km/h)', 'Risk Score', 'Recommended Actions'
    ])
    for i, r in enumerate(rows, 1):
        writer.writerow([
            i,
            r['location'].name,
            r['location'].zone,
            r['accidents'],
            r['fatal'],
            r['avg_level'],
            r['avg_speed'],
            r['score'],
            ' | '.join(r['tips'])
        ])
    return response


@login_required
def api_stats(request):
    """JSON endpoint used by Chart.js on the dashboard."""
    days = int(request.GET.get('days', 30))
    if days not in (7, 14, 30, 60):
        days = 30
    return JsonResponse({
        'summary': analytics.summary_counts(days=days),
        'severity': analytics.accidents_by_severity(days=days),
        'per_day': analytics.accidents_per_day(days=min(days, 30)),
        'by_hour': analytics.congestion_by_hour(days=days),
        'hotspots': [{'name': r['location'].name, 'score': r['score']} for r in analytics.hotspots(days=days, limit=6)],
    })


@login_required
def api_map_data(request):
    """Returns spatial data for all tracked city locations, pins, accidents & congestion levels."""
    since = analytics.recent_window(days=30)
    locations_data = []
    
    for loc in Location.objects.all():
        if loc.latitude is None or loc.longitude is None:
            continue
        acc = loc.accidents.filter(occurred_at__gte=since)
        cong = loc.congestion_reports.filter(reported_at__gte=since)
        latest_cong = cong.first()
        active_alerts = loc.alerts.filter(is_active=True).count()
        acc_points = sum(a.points for a in acc)
        avg_level = cong.aggregate(a=Avg('level'))['a'] or 0
        score = acc_points * 2 + round(avg_level * cong.count() * 0.5, 1)
        
        locations_data.append({
            'id': loc.id,
            'name': loc.name,
            'zone': loc.zone,
            'lat': float(loc.latitude),
            'lng': float(loc.longitude),
            'accidents': acc.count(),
            'fatal': acc.filter(severity='Fatal').count(),
            'injuries': sum(a.injuries for a in acc),
            'risk_score': round(score, 1),
            'active_alerts': active_alerts,
            'latest_level': latest_cong.level if latest_cong else 1,
            'latest_level_name': latest_cong.get_level_display() if latest_cong else 'Normal',
            'latest_speed': latest_cong.average_speed if latest_cong else 45,
            'latest_cause': latest_cong.cause if latest_cong else 'Free flow',
        })
        
    return JsonResponse({'locations': locations_data})


@login_required
def profile(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    user_form = UserUpdateForm(request.POST or None, instance=request.user, prefix='u')
    prof_form = ProfileForm(request.POST or None, instance=prof, prefix='p')
    if request.method == 'POST' and user_form.is_valid() and prof_form.is_valid():
        user_form.save()
        prof_form.save()
        messages.success(request, 'Your profile details have been saved.')
        return redirect('profile')
    
    reports_count = Accident.objects.filter(reporter=request.user).count()
    congestion_count = CongestionReport.objects.filter(reporter=request.user).count()
    
    return render(request, 'management_app/profile.html', {
        'user_form': user_form,
        'prof_form': prof_form,
        'pw_form': PasswordChangeForm(request.user),
        'reports_count': reports_count,
        'congestion_count': congestion_count,
    })


@login_required
@require_POST
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password successfully updated.')
    else:
        err_msg = ' '.join(sum(form.errors.values(), []))
        messages.error(request, f'Password error: {err_msg}')
    return redirect('profile')


@login_required
def api_gemini_status(request):
    """Checks whether Gemini API is active and configured."""
    return JsonResponse({
        'configured': gemini_service.is_gemini_configured(),
        'masked_key': (gemini_service.get_gemini_api_key()[:6] + '...' + gemini_service.get_gemini_api_key()[-4:]) if gemini_service.is_gemini_configured() else ''
    })


@login_required
@require_POST
def api_gemini_analyze_accident(request, pk):
    """Analyzes a specific accident case using Gemini AI."""
    obj = get_object_or_404(Accident.objects.select_related('location'), pk=pk)
    result = gemini_service.analyze_accident_report(obj)
    return JsonResponse(result)


@login_required
@require_POST
def api_gemini_copilot(request):
    """Answers traffic safety, hotspot and municipal inquiries via Gemini."""
    query = request.POST.get('query', '').strip()
    if not query:
        return JsonResponse({'success': False, 'error': 'Query cannot be empty.'})
    
    summary = (
        f"City: Amritsar Traffic Surveillance Grid. Active junctions: 10.\n"
        f"Recent 30-day Accidents: {Accident.objects.count()}.\n"
        f"Fatal Incidents: {Accident.objects.filter(severity='Fatal').count()}.\n"
        f"Active Alerts: {Alert.objects.filter(is_active=True).count()}."
    )
    result = gemini_service.copilot_query(query, summary)
    return JsonResponse(result)


@login_required
@require_POST
def api_gemini_save_key(request):
    """Allows user/officer to save and activate Gemini API Key directly from UI."""
    key = request.POST.get('api_key', '').strip()
    if not key:
        return JsonResponse({'success': False, 'error': 'API key cannot be empty.'})
    
    from django.conf import settings
    settings.GEMINI_API_KEY = key
    import os
    os.environ['GEMINI_API_KEY'] = key

    # Write to .env in BASE_DIR
    env_path = settings.BASE_DIR / '.env'
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f"# TrafficSafe Environment Configuration\nGEMINI_API_KEY={key}\n")
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to write to .env: {str(e)}'})
        
    return JsonResponse({'success': True, 'message': 'Gemini API Key successfully saved and activated!'})

