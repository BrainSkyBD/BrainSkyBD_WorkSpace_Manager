# monitor/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
from django.db.models import Sum

def screenshot_upload_path(instance, filename):
    # Organize by user/year/month/day/hour
    date_path = timezone.now().strftime("%Y/%m/%d/%H")
    return os.path.join('screenshots', str(instance.user.id), date_path, filename)


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TrackingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    total_time = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"Session for {self.user.username} started at {self.start_time}"

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            # Make sure both datetimes are timezone-aware
            if timezone.is_naive(self.start_time):
                self.start_time = timezone.make_aware(self.start_time)
            if timezone.is_naive(self.end_time):
                self.end_time = timezone.make_aware(self.end_time)
            self.total_time = self.end_time - self.start_time
        super().save(*args, **kwargs)

    @classmethod
    def get_time_summary(cls, date_from=None, date_to=None, user_id=None, project_id=None):
        queryset = cls.objects.filter(is_active=False)

        if date_from:
            queryset = queryset.filter(start_time__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_time__date__lte=date_to)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset.values('user__username', 'project__name').annotate(
            total_time=Sum('total_time')
        ).order_by('user__username', 'project__name')


class Screenshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    tracking_session = models.ForeignKey(TrackingSession, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to=screenshot_upload_path)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            self.file_size = self.image.size
            super().save(update_fields=['file_size'])

    def __str__(self):
        return f"Screenshot for {self.user.username} at {self.timestamp}"

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(TrackingSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    screenshot = models.ForeignKey(Screenshot, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]