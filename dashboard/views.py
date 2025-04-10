from django.shortcuts import render
from django.contrib.auth.models import User
# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from monitor.models import Screenshot, TrackingSession

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from monitor.models import Screenshot, TrackingSession, Project
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from monitor.models import TrackingSession
from datetime import timedelta
from django.db.models import Sum, F, Func, Value, CharField
from django.db.models.functions import Concat
# dashboard/views.py
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone

from monitor.utils.activity import get_user_activity


@login_required
def dashboard(request):
    active_session = TrackingSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    if active_session:
        # Ensure start_time is timezone aware
        if timezone.is_naive(active_session.start_time):
            active_session.start_time = timezone.make_aware(active_session.start_time)
            active_session.save()

    screenshots = Screenshot.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]

    projects = Project.objects.filter(is_active=True)

    context = {
        'active_session': active_session,
        'screenshots': screenshots,
        'projects': projects,
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
@login_required
def time_report(request):
    sessions = TrackingSession.objects.filter(user=request.user).order_by('-start_time')

    # Calculate total time per project
    projects_time = {}
    # Calculate daily totals
    daily_totals = {}

    for session in sessions:
        if session.project:
            # Project totals
            if session.project.name not in projects_time:
                projects_time[session.project.name] = session.total_time or timedelta()
            else:
                projects_time[session.project.name] += session.total_time or timedelta()

            # Daily totals
            date_str = session.start_time.date().isoformat()
            if date_str not in daily_totals:
                daily_totals[date_str] = session.total_time or timedelta()
            else:
                daily_totals[date_str] += session.total_time or timedelta()

    # Convert to list of tuples for template
    projects_time_list = [(project, time) for project, time in projects_time.items()]
    daily_totals_list = [(date, total) for date, total in daily_totals.items()]

    context = {
        'sessions': sessions,
        'projects_time': projects_time_list,
        'daily_totals': daily_totals_list,
    }

    return render(request, 'dashboard/time_report.html', context)





@user_passes_test(lambda u: u.is_superuser)
def admin_analytics(request):
    # Default filter values
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    user_id = request.GET.get('user_id')
    project_id = request.GET.get('project_id')

    # Convert dates to datetime objects
    try:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        date_from = (timezone.now() - timedelta(days=7)).date()
        date_to = timezone.now().date()

    # Build filters
    filters = Q(timestamp__date__gte=date_from, timestamp__date__lte=date_to)
    if user_id:
        filters &= Q(user_id=user_id)
    if project_id:
        filters &= Q(project_id=project_id)

    # Get analytics data
    time_by_user_project = TrackingSession.get_time_summary(
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        project_id=project_id
    )

    screenshots = Screenshot.objects.filter(filters).order_by('-timestamp')

    # Get filter options
    users = User.objects.all()
    projects = Project.objects.all()

    # Add activity data to context
    users_data = []
    for user in User.objects.filter(is_staff=True):
        users_data.append({
            'user': user,
            'activity': get_user_activity(user)
        })

    context = {
        'time_by_user_project': time_by_user_project,
        'screenshots': screenshots,
        'users': users,
        'projects': projects,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'selected_user': int(user_id) if user_id else None,
        'selected_project': int(project_id) if project_id else None,
        'users_data': users_data,
    }

    return render(request, 'dashboard/admin_analytics.html', context)


@login_required
def staff_analytics(request):
    # Default filter values - only show current user's data
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    project_id = request.GET.get('project_id')

    # Convert dates to datetime objects
    try:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        date_from = (timezone.now() - timedelta(days=7)).date()
        date_to = timezone.now().date()

    # Build filters - always filter by current user
    filters = Q(
        user=request.user,
        timestamp__date__gte=date_from,
        timestamp__date__lte=date_to
    )

    if project_id:
        filters &= Q(project_id=project_id)

    # Get analytics data
    time_by_project = (
        TrackingSession.objects
        .filter(
            user=request.user,
            start_time__date__gte=date_from,
            end_time__date__lte=date_to
        )
        .values('project__name')
        .annotate(total_time=Sum('total_time'))
        .order_by('project__name')
    )

    # Get filter options (only projects this user has worked on)
    projects = Project.objects.filter(
        id__in=TrackingSession.objects.filter(user=request.user)
        .values_list('project_id', flat=True).distinct()
    )

    context = {
        'time_by_project': time_by_project,
        'projects': projects,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'selected_project': int(project_id) if project_id else None,
    }

    return render(request, 'dashboard/staff_analytics.html', context)


