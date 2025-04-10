"""
URL configuration for tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from monitor import views as monitor_views
from dashboard import views as dashboard_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_views.dashboard, name='dashboard'),
    path('start/', monitor_views.start_tracking, name='start_tracking'),
    path('stop/', monitor_views.stop_tracking, name='stop_tracking'),
    path('time-report/', dashboard_views.time_report, name='time_report'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin-analytics/', user_passes_test(lambda u: u.is_superuser)(dashboard_views.admin_analytics), name='admin_analytics'),
    path('staff-analytics/', login_required(dashboard_views.staff_analytics), name='staff_analytics'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)