import logging
import signal
import sys
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from telemetry.models import TelemetryReading, TelemetrySensor
from telemetry.quality import evaluate_and_alert

logger = logging.getLogger(__name__)

_shutdown_requested = False


def _handle_signal(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True


class Command(BaseCommand):
    help = "Ingest telemetry from external sources (Modbus TCP / Simulator)"

    def add_arguments(self, parser):
        parser.add_argument("--source", default="simulator", choices=["modbus", "simulator"])
        parser.add_argument("--interval", type=float, default=5.0, help="Seconds between reads")
        parser.add_argument("--batch-size", type=int, default=10, help="Max samples per read")

        # Modbus args
        parser.add_argument("--modbus-host", default="127.0.0.1")
        parser.add_argument("--modbus-port", type=int, default=502)
        parser.add_argument("--modbus-unit", type=int, default=1)
        parser.add_argument("--modbus-timeout", type=float, default=5.0)

        # Simulator args
        parser.add_argument("--sim-seed", type=int, default=42)
        parser.add_argument("--sim-count", type=int, default=10)
        parser.add_argument("--sim-anomaly-rate", type=float, default=0.0)

        # One-shot
        parser.add_argument("--once", action="store_true", help="Single read, no loop")

    def handle(self, *args, **options):
        global _shutdown_requested
        _shutdown_requested = False

        source = self._build_source(options)
        if source is None:
            self.stderr.write("Failed to create source")
            return

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        interval = options["interval"]
        batch_size = options["batch_size"]
        iteration = 0
        total_samples = 0
        total_readings = 0

        self.stdout.write(f"Source: {source.name}, interval={interval}s, batch_size={batch_size}")

        try:
            while not _shutdown_requested:
                samples = source.read()
                if not samples:
                    self.stdout.write(f"[{iteration}] No samples from {source.name}")
                else:
                    for sample in samples[:batch_size]:
                        reading = self._sample_to_reading(sample)
                        if reading is not None:
                            evaluate_and_alert(reading)
                            total_readings += 1
                    total_samples += len(samples)
                    self.stdout.write(
                        f"[{iteration}] Read {len(samples)} samples, "
                        f"{total_readings} total readings"
                    )

                iteration += 1
                if options["once"]:
                    break
                if not _shutdown_requested:
                    import time
                    time.sleep(interval)

            health = source.health()
        finally:
            source.close()

        self.stdout.write(
            f"Ingest complete: {total_samples} samples, {total_readings} readings. "
            f"Source health: {health.get('status', 'unknown')}"
        )

    def _build_source(self, options):
        source_type = options["source"]

        if source_type == "modbus":
            from telemetry.sources.modbus import ModbusTCPAdapter

            adapter = ModbusTCPAdapter(
                host=options["modbus_host"],
                port=options["modbus_port"],
                unit_id=options["modbus_unit"],
                timeout=options["modbus_timeout"],
            )
            adapter.connect()
            if not adapter._connected:
                self.stdout.write(self.style.WARNING("Modbus not connected, use --source simulator"))
            return adapter

        if source_type == "simulator":
            from telemetry.sources.simulator import SimulatorAdapter

            return SimulatorAdapter(
                seed=options["sim_seed"],
                count=options["sim_count"],
                anomaly_rate=options["sim_anomaly_rate"],
            )

        return None

    def _sample_to_reading(self, sample):
        try:
            sensor = TelemetrySensor.objects.get(id=sample.sensor_id)
        except TelemetrySensor.DoesNotExist:
            logger.warning("Sensor %d not found, skipping", sample.sensor_id)
            return None

        timestamp = sample.timestamp or datetime.now(timezone.utc)

        return TelemetryReading(
            sensor=sensor,
            timestamp=timestamp,
            raw_value=round(sample.value, 4),
            calibrated_value=round(sample.value, 4),
        )
