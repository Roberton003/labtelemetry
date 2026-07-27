import random
from datetime import UTC, datetime, timedelta

from django.core.management.base import BaseCommand

from telemetry.models import TelemetryReading, TelemetrySensor
from telemetry.quality import evaluate_and_alert
from telemetry.sources.simulator import SENSOR_DEFAULTS, generate_value


class Command(BaseCommand):
    help = "Simulate telemetry sensor readings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sensors",
            type=int,
            default=0,
            help="Create N default sensors if none exist",
        )
        parser.add_argument("--interval-seconds", type=float, default=5.0)
        parser.add_argument("--iterations", type=int, default=10)
        parser.add_argument("--anomaly-rate", type=float, default=0.1)
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument(
            "--once", action="store_true", help="Single batch, no interval wait"
        )

    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        sensors = list(TelemetrySensor.objects.all())
        if not sensors and options["sensors"] > 0:
            for sdef in SENSOR_DEFAULTS:
                TelemetrySensor.objects.get_or_create(
                    name=sdef["name"], parameter=sdef["parameter"]
                )
            sensors = list(TelemetrySensor.objects.all())
            self.stdout.write(f"Criados {len(sensors)} sensores padrao")

        if not sensors:
            self.stderr.write("Nenhum sensor encontrado. Use --sensors N para criar.")
            return

        now = datetime.now(UTC)
        total_readings = 0
        total_alerts = 0

        for i in range(options["iterations"]):
            ts = now + timedelta(seconds=i * options["interval_seconds"])
            batch: list[TelemetryReading] = []
            for sensor in sensors:
                anomaly = rng.random() < options["anomaly_rate"]
                raw = generate_value(sensor.parameter, rng, anomaly)
                calibrated = raw * sensor.calibration_factor
                reading = TelemetryReading(
                    sensor=sensor,
                    timestamp=ts,
                    raw_value=round(raw, 4),
                    calibrated_value=round(calibrated, 4),
                )
                status = evaluate_and_alert(reading)
                batch.append(reading)
                total_readings += 1
                if status != "NORMAL":
                    total_alerts += 1

            TelemetryReading.objects.bulk_create(batch, ignore_conflicts=True)

            if options["once"]:
                break

        self.stdout.write(
            f"Geradas {total_readings} leituras, {total_alerts} anomalias/alertas "
            f"(seed={options['seed']}, anomaly_rate={options['anomaly_rate']})"
        )
