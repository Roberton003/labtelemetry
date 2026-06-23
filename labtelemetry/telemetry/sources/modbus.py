import logging
import socket
from datetime import datetime, timezone

from telemetry.sources.base import TelemetrySample, TelemetrySource

logger = logging.getLogger(__name__)

PARAMETER_MAP: dict[int, str] = {
    0: "PH",
    1: "TURBIDITY",
    2: "TOC",
}


class ModbusTCPAdapter(TelemetrySource):
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 502,
        unit_id: int = 1,
        timeout: float = 5.0,
        client=None,
    ):
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._timeout = timeout
        self._client = client
        self._connected = False
        self._last_read: datetime | None = None

    @property
    def name(self) -> str:
        return f"modbus:{self._host}:{self._port}"

    def connect(self) -> None:
        if self._client is not None:
            self._connected = True
            return

        try:
            from pymodbus.client import ModbusTcpClient

            self._client = ModbusTcpClient(
                host=self._host,
                port=self._port,
                timeout=self._timeout,
            )
            self._client.connect()
            self._connected = True
        except ImportError:
            logger.warning("pymodbus not installed; ModbusTCPAdapter disabled")
            self._connected = False
        except Exception as exc:
            logger.error("Modbus connect failed: %s", exc)
            self._connected = False

    def read(self) -> list[TelemetrySample]:
        if not self._connected:
            self.connect()
        if not self._connected or self._client is None:
            return []

        try:
            result = self._client.read_holding_registers(
                address=0, count=3, slave=self._unit_id
            )
            if result is None or result.isError():
                logger.warning("Modbus read error: %s", result)
                return []

            now = datetime.now(timezone.utc)
            self._last_read = now
            samples: list[TelemetrySample] = []

            for i, param_id in enumerate(sorted(PARAMETER_MAP.keys())):
                raw_value = float(result.registers[i]) if i < len(result.registers) else 0.0
                param = PARAMETER_MAP[param_id]
                samples.append(
                    TelemetrySample(
                        sensor_id=param_id,
                        parameter=param,
                        value=raw_value,
                        timestamp=now,
                        quality="GOOD",
                        source=self.name,
                        raw_payload={"register": param_id, "raw": raw_value},
                    )
                )

            return samples

        except socket.timeout:
            logger.warning("Modbus read timed out")
            return []
        except Exception as exc:
            logger.error("Modbus read failed: %s", exc)
            return []

    def health(self) -> dict:
        return {
            "name": self.name,
            "status": "connected" if self._connected else "disconnected",
            "last_read": self._last_read.isoformat() if self._last_read else None,
            "host": self._host,
            "port": self._port,
        }

    def close(self) -> None:
        if self._client and self._connected:
            try:
                self._client.close()
            except Exception as exc:
                logger.warning("Modbus close error: %s", exc)
        self._connected = False
        self._client = None
