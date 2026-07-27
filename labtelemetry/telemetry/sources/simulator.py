import logging
import random
from datetime import UTC, datetime, timedelta

from telemetry.sources.base import TelemetrySample, TelemetrySource

logger = logging.getLogger(__name__)

BASE_VALUES = {
    "PH": {"mean": 7.0, "std": 0.3},
    "TURBIDITY": {"mean": 2.0, "std": 0.5},
    "TOC": {"mean": 5.0, "std": 1.0},
}

SENSOR_DEFAULTS = [
    {"name": "pH Entrada", "parameter": "PH"},
    {"name": "pH Saída", "parameter": "PH"},
    {"name": "Turbidez Entrada", "parameter": "TURBIDITY"},
    {"name": "Turbidez Saída", "parameter": "TURBIDITY"},
    {"name": "TOC Entrada", "parameter": "TOC"},
    {"name": "TOC Saída", "parameter": "TOC"},
]


def generate_value(parameter: str, rng: random.Random, anomaly: bool = False) -> float:
    cfg = BASE_VALUES.get(parameter, {"mean": 50.0, "std": 10.0})
    if anomaly:
        offset = rng.uniform(-3, 3) * cfg["std"]
        return cfg["mean"] + offset * 3
    return rng.gauss(cfg["mean"], cfg["std"])


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
        from telemetry.models import TelemetrySensor

        sensors = list(TelemetrySensor.objects.all())
        if not sensors:
            for sdef in SENSOR_DEFAULTS:
                TelemetrySensor.objects.get_or_create(
                    name=sdef["name"], parameter=sdef["parameter"]
                )
            sensors = list(TelemetrySensor.objects.all())
            logger.info("Criados %d sensores padrao", len(sensors))

        now = datetime.now(UTC)
        rng = random.Random(self._seed)
        samples: list[TelemetrySample] = []

        for i in range(self._count):
            ts = now + timedelta(seconds=i * 5.0)
            for sensor in sensors:
                anomaly = rng.random() < self._anomaly_rate
                raw = generate_value(sensor.parameter, rng, anomaly)
                samples.append(
                    TelemetrySample(
                        sensor_id=sensor.id,
                        parameter=sensor.parameter,
                        value=round(raw, 4),
                        timestamp=ts,
                        quality="BAD" if anomaly else "GOOD",
                        source=self.name,
                        raw_payload={
                            "raw": round(raw, 4),
                            "anomaly": anomaly,
                        },
                    )
                )

        self._last_read = now
        return samples

    def health(self) -> dict:
        return {
            "name": self.name,
            "status": "ok",
            "last_read": self._last_read.isoformat() if self._last_read else None,
            "seed": self._seed,
            "count": self._count,
        }
