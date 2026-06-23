from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TelemetrySample:
    sensor_id: int
    parameter: str
    value: float
    timestamp: datetime | None = None
    quality: str = "GOOD"
    source: str = "unknown"
    raw_payload: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = field(default_factory=dict)

    QUALITY_MAP = {
        "GOOD": "NORMAL",
        "SUSPECT": "DRIFT_WARNING",
        "BAD": "OUT_OF_BOUNDS",
    }

    def map_quality(self) -> str:
        return self.QUALITY_MAP.get(self.quality, "NORMAL")


QUALITY_MAP = TelemetrySample.QUALITY_MAP


class TelemetrySource(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def read(self) -> list[TelemetrySample]:
        ...

    def health(self) -> dict:
        return {"name": self.name, "status": "unknown", "last_read": None}

    def close(self) -> None:
        pass
