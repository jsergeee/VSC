import signal
import sys
from django.core.management.commands.runserver import Command as BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        def signal_handler(sig, frame):
            self.stdout.write("\nServer stopped gracefully")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        super().handle(*args, **options)