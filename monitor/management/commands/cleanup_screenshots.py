# monitor/management/commands/cleanup_screenshots.py
from django.core.management.base import BaseCommand
from monitor.models import Screenshot
from django.utils import timezone
from datetime import timedelta
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Deletes screenshots older than specified days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete screenshots older than this many days'
        )

    def handle(self, *args, **options):
        days = options['days']
        threshold = timezone.now() - timedelta(days=days)

        # Delete database records and files
        old_screenshots = Screenshot.objects.filter(timestamp__lt=threshold)
        count = old_screenshots.count()

        for screenshot in old_screenshots:
            if screenshot.image:
                path = os.path.join(settings.MEDIA_ROOT, screenshot.image.name)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError as e:
                    self.stdout.write(f"Error deleting {path}: {e}")

        old_screenshots.delete()
        self.stdout.write(f"Deleted {count} old screenshots (older than {days} days)")