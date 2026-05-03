import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from market.tasks import price_tick_task, apply_events_task

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the CRYTX market simulation loop (ticks and events) continuously.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting CRYTX Market Simulation Loop..."))
        
        TICK_INTERVAL = 10
        EVENT_INTERVAL = 30
        
        last_tick = 0
        last_event = 0
        
        try:
            while True:
                now = time.time()
                
                # Run price tick every 10s
                if now - last_tick >= TICK_INTERVAL:
                    self.stdout.write(f"[{timezone.now().isoformat()}] Running price_tick_task...")
                    price_tick_task()
                    last_tick = now
                
                # Run events check every 30s
                if now - last_event >= EVENT_INTERVAL:
                    self.stdout.write(f"[{timezone.now().isoformat()}] Running apply_events_task...")
                    apply_events_task()
                    last_event = now
                
                # Sleep a bit to prevent CPU spinning
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nStopping Market Simulation Loop."))
