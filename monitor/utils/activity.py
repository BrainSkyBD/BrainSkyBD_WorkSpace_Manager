from datetime import timedelta
from django.utils import timezone
from monitor.models import ActivityLog


def get_user_activity(user):
    """Calculate user activity status (only called by admin views)"""
    last_log = ActivityLog.objects.filter(user=user).order_by('-timestamp').first()
    if not last_log:
        return {'active': False, 'rate': 0, 'last_seen': None}

    # Check last 1 minutes activity
    cutoff = timezone.now() - timedelta(minutes=1)
    logs = ActivityLog.objects.filter(
        user=user,
        timestamp__gte=cutoff
    )

    active_count = logs.filter(is_active=True).count()
    total_count = logs.count()
    activity_rate = round((active_count / total_count * 100)) if total_count else 0

    return {
        'active': activity_rate > 50,
        'rate': activity_rate,
        'last_seen': last_log.timestamp
    }