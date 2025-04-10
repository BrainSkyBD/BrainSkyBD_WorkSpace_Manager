from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Screenshot, TrackingSession
from django.contrib import admin
from .models import Project, Screenshot, TrackingSession

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)

@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'timestamp', 'is_active')
    list_filter = ('user', 'project', 'is_active')

@admin.register(TrackingSession)
class TrackingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'start_time', 'end_time', 'total_time', 'is_active')
    list_filter = ('user', 'project', 'is_active')
