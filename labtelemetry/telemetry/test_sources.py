from django.test import TestCase, tag

from telemetry.models import TelemetryReading, TelemetrySensor
from telemetry.sources.base import TelemetrySample
from telemetry.sources.modbus import ModbusTCPAdapter
from telemetry.sources.opcua import OpcUaAdapter
from telemetry.sources.opcua_test_server import (
    ALL_NODE_IDS,
    DEFAULT_PORT,
    run_test_server,
)
from telemetry.sources.simulator import SimulatorAdapter


class TelemetrySampleTest(TestCase):
    def test_default_quality_maps_to_normal(self):
        s = TelemetrySample(sensor_id=1, parameter="PH", value=7.0)
        self.assertEqual(s.map_quality(), "NORMAL")

    def test_suspect_maps_to_drift_warning(self):
        s = TelemetrySample(sensor_id=1, parameter="PH", value=8.6, quality="SUSPECT")
        self.assertEqual(s.map_quality(), "DRIFT_WARNING")

    def test_bad_maps_to_out_of_bounds(self):
        s = TelemetrySample(sensor_id=1, parameter="PH", value=9.0, quality="BAD")
        self.assertEqual(s.map_quality(), "OUT_OF_BOUNDS")

    def test_unknown_quality_defaults_to_normal(self):
        s = TelemetrySample(sensor_id=1, parameter="PH", value=7.0, quality="UNKNOWN")
        self.assertEqual(s.map_quality(), "NORMAL")


class SimulatorAdapterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i, param in enumerate(["PH", "TURBIDITY", "TOC"]):
            TelemetrySensor.objects.create(
                id=i + 1,
                name=f"Sensor {param}",
                parameter=param,
            )

    def test_health_returns_metadata(self):
        adapter = SimulatorAdapter(seed=42, count=5)
        health = adapter.health()
        self.assertEqual(health["name"], "simulator:seed=42")
        self.assertIn("last_read", health)

    def test_read_returns_samples_without_db_roundtrip(self):
        adapter = SimulatorAdapter(seed=42, count=3)
        samples = adapter.read()
        # count=3, 3 sensors from setUpTestData = 9 samples
        self.assertEqual(len(samples), 9)
        self.assertIsInstance(samples[0], TelemetrySample)
        # Adapter generates raw values — does NOT persist to DB
        self.assertEqual(TelemetryReading.objects.count(), 0)
        # Verify source metadata
        self.assertEqual(samples[0].source, "simulator:seed=42")
        # Same seed -> same deterministic values
        adapter2 = SimulatorAdapter(seed=42, count=3)
        samples2 = adapter2.read()
        self.assertEqual(len(samples2), 9)
        self.assertEqual(samples2[0].value, samples2[0].value)


class _FakeModbusResult:
    def __init__(self, registers, error=False):
        self.registers = registers
        self._error = error

    def isError(self):  # noqa: N802 — mocka pymodbus
        return self._error


class _FakeModbusClient:
    def __init__(self, registers):
        self._registers = registers
        self.closed = False

    def read_holding_registers(self, address, count, slave):
        return _FakeModbusResult(self._registers[:count])

    def close(self):
        self.closed = True


class ModbusAdapterTest(TestCase):
    def test_read_maps_registers_and_preserves_source_metadata(self):
        adapter = ModbusTCPAdapter(
            host="plc.local",
            port=1502,
            unit_id=7,
            timeout=0.25,
            client=_FakeModbusClient([7, 3, 12]),
        )

        samples = adapter.read()

        self.assertEqual(len(samples), 3)
        self.assertEqual(samples[0].sensor_id, 0)
        self.assertEqual(samples[0].parameter, "PH")
        self.assertEqual(samples[0].source, "modbus:plc.local:1502")
        self.assertEqual(samples[0].raw_payload, {"register": 0, "raw": 7.0})
        self.assertEqual(samples[1].parameter, "TURBIDITY")
        self.assertEqual(samples[2].parameter, "TOC")
        self.assertEqual(adapter.health()["status"], "connected")

        adapter.close()
        self.assertFalse(adapter._connected)


class OpcUaAdapterTest(TestCase):
    def test_health_returns_metadata_before_read(self):
        from telemetry.sources.opcua import OpcUaAdapter

        adapter = OpcUaAdapter(url="opc.tcp://localhost:14840", node_ids=["ns=2;i=1"])
        health = adapter.health()
        self.assertEqual(health["name"], "opcua:opc.tcp://localhost:14840")
        self.assertEqual(health["status"], "unknown")
        self.assertIsNone(health["last_read"])
        self.assertEqual(health["nodes"], 1)

    def test_read_returns_empty_on_connection_error(self):
        adapter = OpcUaAdapter(
            url="opc.tcp://127.0.0.1:1",  # unlikely to have a server here
            node_ids=["ns=2;i=1"],
            timeout=0.25,
        )
        samples = adapter.read()
        self.assertEqual(samples, [])
        self.assertIsNone(adapter.health()["last_read"])

    @tag("integration")
    def test_read_with_live_server_returns_samples(self):
        """Integration test: start OPC-UA server, connect, read values."""
        import time

        thread = run_test_server(DEFAULT_PORT)
        try:
            adapter = OpcUaAdapter(
                url=f"opc.tcp://127.0.0.1:{DEFAULT_PORT}",
                node_ids=ALL_NODE_IDS,
                timeout=5.0,
            )
            # Retry up to 3x to account for server startup latency
            samples = []
            for _ in range(3):
                samples = adapter.read()
                if len(samples) == 3:
                    break
                time.sleep(1)
            self.assertEqual(len(samples), 3)
            self.assertEqual(samples[0].parameter, "PH")
            self.assertAlmostEqual(samples[0].value, 7.0, delta=0.1)
            self.assertEqual(samples[1].parameter, "TURBIDITY")
            self.assertAlmostEqual(samples[1].value, 2.0, delta=0.1)
            self.assertEqual(samples[2].parameter, "TOC")
            self.assertAlmostEqual(samples[2].value, 5.0, delta=0.1)
            # Verify source metadata
            self.assertIn("opcua:opc.tcp://127.0.0.1", samples[0].source)
            health = adapter.health()
            self.assertEqual(health["nodes"], 3)
            self.assertIsNotNone(health["last_read"])
        finally:
            thread.join(timeout=2)
