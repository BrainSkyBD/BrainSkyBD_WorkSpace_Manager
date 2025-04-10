from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Screenshot, TrackingSession, Project
from django.conf import settings
import os

from datetime import datetime
import time
from threading import Thread
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Screenshot, TrackingSession, Project
from django.conf import settings
import os
from PIL import ImageGrab  # Replace pyautogui with this
from datetime import datetime
import time
from threading import Thread
from django.utils import timezone
from PIL import Image
import io

import numpy as np
from monitor.models import ActivityLog


@login_required
def start_tracking(request):
    if request.method == 'POST':
        project_id = request.POST.get('project')
        if not project_id:
            messages.error(request, 'Please select a project')
            return redirect('dashboard')

        project = get_object_or_404(Project, id=project_id)

        active_session = TrackingSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not active_session:
            session = TrackingSession.objects.create(
                user=request.user,
                project=project
            )

            thread = Thread(
                target=take_screenshots,
                args=(request.user, session.id, project.id)
            )
            thread.daemon = True
            thread.start()

            messages.success(request, f'Tracking started for project: {project.name}!')
        else:
            messages.warning(request, 'Tracking is already active!')

    return redirect('dashboard')


@login_required
def stop_tracking(request):
    active_session = TrackingSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if active_session:
        active_session.is_active = False
        active_session.end_time = timezone.now()
        active_session.save()

        Screenshot.objects.filter(
            user=request.user,
            is_active=True,
            tracking_session=active_session
        ).update(is_active=False)

        messages.success(request, f'Tracking stopped for project: {active_session.project.name}!')
    else:
        messages.warning(request, 'No active tracking session found!')

    return redirect('dashboard')




def take_screenshots(user, session_id, project_id):
    session = TrackingSession.objects.get(id=session_id)
    project = Project.objects.get(id=project_id)
    last_screenshot = None  # To store the previous screenshot for comparison

    while session.is_active:
        try:
            # Take screenshot using Pillow's ImageGrab (works on Linux with Xvfb)
            screenshot = ImageGrab.grab()  # <-- REPLACED pyautogui.screenshot()

            # Activity detection - compare with previous screenshot if exists
            is_active = True  # Default to active
            if last_screenshot:
                # Convert screenshots to numpy arrays for comparison
                current_img = np.array(screenshot)
                last_img = np.array(last_screenshot)

                # Calculate absolute difference between images
                diff = np.abs(current_img.astype("int32") - last_img.astype("int32"))

                # Count significantly changed pixels (threshold of 25 out of 255)
                changed_pixels = np.sum(diff > 25)
                total_pixels = current_img.shape[0] * current_img.shape[1]

                # If less than 1% of pixels changed, consider inactive
                if (changed_pixels / total_pixels) < 0.01:
                    is_active = False

            # Optimize image (same as before)
            img_byte_arr = io.BytesIO()
            if screenshot.size[0] > 1920:
                new_height = int(1920 * screenshot.size[1] / screenshot.size[0])
                screenshot = screenshot.resize((1920, new_height), Image.Resampling.LANCZOS)
            screenshot.save(img_byte_arr, format='WEBP', quality=85)

            # Save to database (same as before)
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'screenshot_{user.username}_{project.name}_{timestamp}.webp'
            screenshot_obj = Screenshot(user=user, project=project, tracking_session=session)
            screenshot_obj.image.save(filename, img_byte_arr)
            screenshot_obj.save()

            # Log activity (same as before)
            ActivityLog.objects.create(
                user=user,
                session=session,
                is_active=is_active,
                screenshot=screenshot_obj
            )

            last_screenshot = screenshot  # Update for next comparison
            time.sleep(30)
            session.refresh_from_db()

        except Exception as e:
            print(f"Error taking screenshot: {e}")
            ActivityLog.objects.create(user=user, session=session, is_active=False, screenshot=None)
            time.sleep(30)
            session.refresh_from_db()

def get_storage_usage(user):
    from django.db.models import Sum
    return Screenshot.objects.filter(user=user).aggregate(
        total=Sum('file_size')
    )['total'] or 0

