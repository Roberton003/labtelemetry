import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from telemetry.sources.base import TelemetrySample, TelemetrySource

logger = logging.getLogger(__name__)

PARAMETER_MAP: dict[int, str] = {
    0: "PH",
    1: "TURBIDITY",
    2: "TOC",
}


@dataclass(frozen=True)
class RegisterSpec:
    """Um holding register e o ponto que ele alimenta.

    `scale` existe porque holding register e uint16: um pH de 7.23 nao cabe
    nele. O CLP publica 723 e o campo diz como voltar para a grandeza fisica
    (723 * 0.01). Sem isso o valor chega inteiro e silenciosamente errado.
    """

    address: int
    sensor_id: int
    scale: float = 1.0
    parameter: str = ""


class ModbusTCPAdapter(TelemetrySource):
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 502,
        unit_id: int = 1,
        timeout: float = 5.0,
        client=None,
        registers: list[RegisterSpec] | None = None,
    ):
        """Adapter Modbus TCP.

        `registers` mapeia cada holding register ao TelemetrySensor que ele
        alimenta. Sem ele, cai no PARAMETER_MAP legado (registers 0/1/2 ->
        "sensor" 0/1/2), que trata indice de registrador como chave primaria
        de sensor — util so para inspecao, nunca para ingestao.
        """
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._timeout = timeout
        self._client = client
        self._connected = False
        self._last_read: datetime | None = None
        self._registers = registers

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
            if self._registers is not None:
                return self._read_configured()
            return self._read_legacy()

        except TimeoutError:
            logger.warning("Modbus read timed out")
            return []
        except Exception as exc:
            logger.error("Modbus read failed: %s", exc)
            return []

    def _read_configured(self) -> list[TelemetrySample]:
        """Le cada registrador configurado e aplica a escala do ponto."""
        now = datetime.now(UTC)
        samples: list[TelemetrySample] = []

        for spec in self._registers or []:
            # ponytail: uma leitura por registrador. Enderecos esparsos tornam
            # a leitura em bloco invalida em muitos CLPs (registrador nao
            # mapeado no meio do span). Se o numero de pontos crescer a ponto
            # de os round trips pesarem, agrupar faixas contiguas.
            result = self._client.read_holding_registers(
                address=spec.address, count=1, slave=self._unit_id
            )
            if result is None or result.isError():
                logger.warning(
                    "Modbus read error no registrador %d: %s", spec.address, result
                )
                continue

            raw = float(result.registers[0])
            value = raw * spec.scale
            samples.append(
                TelemetrySample(
                    sensor_id=spec.sensor_id,
                    parameter=spec.parameter,
                    value=value,
                    timestamp=now,
                    quality="GOOD",
                    source=self.name,
                    raw_payload={
                        "register": spec.address,
                        "raw": raw,
                        "scale": spec.scale,
                    },
                )
            )

        if samples:
            self._last_read = now
        return samples

    def _read_legacy(self) -> list[TelemetrySample]:
        """Leitura em bloco dos registers 0-2, sem mapeamento de sensor.

        Mantido para inspecao rapida de um CLP. O `sensor_id` aqui e o indice
        do registrador, nao uma chave primaria — nao usar para ingestao.
        """
        result = self._client.read_holding_registers(
            address=0, count=3, slave=self._unit_id
        )
        if result is None or result.isError():
            logger.warning("Modbus read error: %s", result)
            return []

        now = datetime.now(UTC)
        self._last_read = now
        samples: list[TelemetrySample] = []

        for i, param_id in enumerate(sorted(PARAMETER_MAP.keys())):
            raw_value = float(result.registers[i]) if i < len(result.registers) else 0.0
            samples.append(
                TelemetrySample(
                    sensor_id=param_id,
                    parameter=PARAMETER_MAP[param_id],
                    value=raw_value,
                    timestamp=now,
                    quality="GOOD",
                    source=self.name,
                    raw_payload={"register": param_id, "raw": raw_value},
                )
            )

        return samples

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
