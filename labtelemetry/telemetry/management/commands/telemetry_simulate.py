from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compatibility wrapper for simulate_telemetry"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--count", type=int, default=50)
        parser.add_argument("--sensors", type=int, default=6)
        parser.add_argument("--anomaly-rate", type=float, default=0.1)

    def handle(self, *args, **options):
        command_args = [
            "simulate_telemetry",
            "--sensors",
            str(options["sensors"]),
            "--iterations",
            str(options["count"]),
            "--anomaly-rate",
            str(options["anomaly_rate"]),
        ]
        if options["seed"] is not None:
            command_args.extend(["--seed", str(options["seed"])])

        call_command(
            *command_args,
            stdout=self.stdout,
            stderr=self.stderr,
        )
