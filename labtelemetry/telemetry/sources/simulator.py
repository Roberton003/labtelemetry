import logging
from datetime import datetime, timezone
from io import StringIO
from typing import Any

from django.core.management import call_command

from telemetry.sources.base import TelemetrySample, TelemetrySource

logger = logging.getLogger(__name__)


class SimulatorAdapter(TelemetrySource):
    def __init__(self, seed: int = 42, count: int = 10, anomaly_rate: float = 0.0):
        self._seed = seed
        self._count = count
        self._anomaly_rate = anomaly_rate
        self._last_read: datetime | None = None

    @property
    def name(self) -> str:
        return f"simulator:seed={self._seed}"

    def read(self) -> list[TelemetrySample]:
        buf = StringIO()
        try:
            call_command(
                "telemetry_simulate",
                seed=self._seed,
                count=self._count,
                anomaly_rate=str(self._anomaly_rate),
                stdout=buf,
            )
        except Exception as exc:
            logger.error("Simulator read failed: %s", exc)
            return []

        now = datetime.now(timezone.utc)
        self._last_read = now
        output = buf.getvalue().strip()

        samples: list[TelemetrySample] = []
        reading_map = self._parse_last_readings()

        for sensor_id, reading in reading_map.items():
            is_anomaly = reading.get("status", "NORMAL") != "NORMAL"
            samples.append(
                TelemetrySample(
                    sensor_id=sensor_id,
                    parameter=reading.get("parameter", "UNKNOWN"),
                    value=reading.get("calibrated_value", 0.0),
                    timestamp=reading.get("timestamp", now),
                    quality="BAD" if is_anomaly else "GOOD",
                    source=self.name,
                    raw_payload=reading,
                    metadata={"output": output},
                )
            )

        return samples

    def _parse_last_readings(self) -> dict[int, dict[str, Any]]:
        from telemetry.models import TelemetryReading

        latest = (
            TelemetryReading.objects.select_related("sensor")
            .order_by("sensor_id", "-timestamp")
        )
        result: dict[int, dict[str, Any]] = {}
        seen: set[int] = set()
        for r in latest:
            if r.sensor_id in seen:
                continue
            seen.add(r.sensor_id)
            result[r.sensor_id] = {
                "parameter": r.sensor.parameter,
                "value": r.raw_value,
                "calibrated_value": r.calibrated_value,
                "status": r.status,
                "timestamp": r.timestamp,
            }
        return result

    def health(self) -> dict:
        return {
            "name": self.name,
            "status": "ok",
            "last_read": self._last_read.isoformat() if self._last_read else None,
            "seed": self._seed,
            "count": self._count,
        }
