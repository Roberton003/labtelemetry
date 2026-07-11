import asyncio
import logging
from datetime import UTC, datetime

from telemetry.sources.base import TelemetrySample, TelemetrySource

logger = logging.getLogger(__name__)


class OpcUaAdapter(TelemetrySource):
    """OPC-UA client adapter.

    Reads node values from an OPC-UA server and returns TelemetrySample list.
    Connects/disconnects per read() call using asyncio.run() internally.
    """

    def __init__(
        self,
        url: str = "opc.tcp://localhost:4840",
        node_ids: list[str] | None = None,
        timeout: float = 5.0,
    ):
        self._url = url
        self._node_ids = node_ids or []
        self._timeout = timeout
        self._last_read: datetime | None = None

    @property
    def name(self) -> str:
        return f"opcua:{self._url}"

    def read(self) -> list[TelemetrySample]:
        try:
            return asyncio.run(self._async_read())
        except Exception as exc:
            logger.error("OPC-UA read failed: %s", exc)
            return []

    async def _async_read(self) -> list[TelemetrySample]:
        from asyncua import Client as OpcUaClient

        async with OpcUaClient(url=self._url, timeout=self._timeout) as client:
            samples: list[TelemetrySample] = []
            now = datetime.now(UTC)

            for idx, node_id in enumerate(self._node_ids):
                try:
                    node = client.get_node(node_id)
                    value = await node.read_value()
                    browse_name = (await node.read_browse_name()).Name

                    samples.append(
                        TelemetrySample(
                            sensor_id=idx,
                            parameter=browse_name,
                            value=round(float(value), 4),
                            timestamp=now,
                            source=self.name,
                            raw_payload={"node_id": node_id, "raw": float(value)},
                        )
                    )
                except Exception as exc:
                    logger.warning("OPC-UA node %s read error: %s", node_id, exc)

            self._last_read = now
            return samples

    def health(self) -> dict:
        return {
            "name": self.name,
            "status": "ok" if self._last_read is not None else "unknown",
            "last_read": self._last_read.isoformat() if self._last_read else None,
            "url": self._url,
            "nodes": len(self._node_ids),
        }

    def close(self) -> None:
        self._last_read = None
