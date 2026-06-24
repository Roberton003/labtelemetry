from datetime import datetime, timezone

from django.test import TestCase

from telemetry.sources.base import TelemetrySample
from telemetry.sources.modbus import ModbusTCPAdapter
from telemetry.sources.simulator import SimulatorAdapter
from telemetry.models import TelemetrySensor, TelemetryReading


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

    def test_read_returns_samples_when_readings_exist(self):
        sensor = TelemetrySensor.objects.first()
        TelemetryReading.objects.create(
            sensor=sensor,
            timestamp=datetime.now(timezone.utc),
            raw_value=7.0,
            calibrated_value=7.0,
        )
        adapter = SimulatorAdapter(seed=42, count=5)
        samples = adapter.read()
        self.assertIsInstance(samples, list)
        if samples:
            self.assertIsInstance(samples[0], TelemetrySample)
            self.assertEqual(samples[0].quality, "GOOD")


class _FakeModbusResult:
    def __init__(self, registers, error=False):
        self.registers = registers
        self._error = error

    def isError(self):
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
