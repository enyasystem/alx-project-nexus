from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import StockReservation


class Command(BaseCommand):
    help = 'Expire active stock reservations whose expires_at passed and release inventory.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not modify DB, just show count')

    def handle(self, *args, **options):
        now = timezone.now()
        qs = StockReservation.objects.filter(status='active', expires_at__isnull=False, expires_at__lte=now)
        count = qs.count()
        self.stdout.write(f'Found {count} expired reservations.')
        if options.get('dry_run'):
            return
        released = 0
        for r in qs:
            try:
                r.release()
                released += 1
            except Exception as exc:
                self.stderr.write(f'Failed to release reservation {r.id}: {exc}')
        self.stdout.write(f'Released {released} reservations.')
\n
