from datetime import datetime, timezone
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from telemetry.models import TelemetryAlert, TelemetryReading, TelemetrySensor
from telemetry.sources.base import TelemetrySample


class _StubSource:
    def __init__(self, name, samples, health=None):
        self._name = name
        self._samples = list(samples)
        self._health = health or {"name": name, "status": "ok", "last_read": None}
        self.closed = False

    @property
    def name(self):
        return self._name

    def read(self):
        return list(self._samples)

    def health(self):
        return dict(self._health)

    def close(self):
        self.closed = True


class _FakeModbusAdapter:
    instances = []

    def __init__(self, host="127.0.0.1", port=502, unit_id=1, timeout=5.0, client=None):
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._timeout = timeout
        self._client = client
        self._connected = False
        self.closed = False
        self._last_read = None
        _FakeModbusAdapter.instances.append(self)

    @property
    def name(self):
        return f"modbus:{self._host}:{self._port}"

    def connect(self):
        self._connected = True

    def read(self):
        if not self._connected:
            return []
        self._last_read = datetime.now(timezone.utc)
        return [
            TelemetrySample(
                sensor_id=1,
                parameter="PH",
                value=7.4,
                timestamp=self._last_read,
                source=self.name,
                raw_payload={"register": 0, "raw": 7.4},
            )
        ]

    def health(self):
        return {
            "name": self.name,
            "status": "connected" if self._connected else "disconnected",
            "last_read": self._last_read.isoformat() if self._last_read else None,
            "host": self._host,
            "port": self._port,
        }

    def close(self):
        self.closed = True
        self._connected = False


class IngestTelemetryCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sensor_ph = TelemetrySensor.objects.create(id=1, name="Sensor pH", parameter="PH")
        cls.sensor_turb = TelemetrySensor.objects.create(id=2, name="Sensor Turbidez", parameter="TURBIDITY")

    def test_once_with_stub_source_persists_readings_and_alerts(self):
        source = _StubSource(
            "stub:simulator",
            [
                TelemetrySample(
                    sensor_id=self.sensor_ph.id,
                    parameter=self.sensor_ph.parameter,
                    value=7.0,
                    timestamp=datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc),
                    source="stub:simulator",
                    raw_payload={"value": 7.0},
                ),
                TelemetrySample(
                    sensor_id=self.sensor_turb.id,
                    parameter=self.sensor_turb.parameter,
                    value=6.5,
                    timestamp=datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc),
                    source="stub:simulator",
                    raw_payload={"value": 6.5},
                ),
            ],
            health={"name": "stub:simulator", "status": "ok", "last_read": "2026-06-23T12:00:00+00:00"},
        )

        out = StringIO()
        with mock.patch("telemetry.management.commands.ingest_telemetry.Command._build_source", return_value=source):
            call_command("ingest_telemetry", "--source", "simulator", "--once", stdout=out)

        self.assertTrue(source.closed)
        self.assertEqual(TelemetryReading.objects.count(), 2)
        self.assertEqual(TelemetryAlert.objects.count(), 1)
        reading = TelemetryReading.objects.get(sensor=self.sensor_turb)
        self.assertEqual(reading.status, "OUT_OF_BOUNDS")
        self.assertEqual(reading.source, "stub:simulator")
        self.assertIn("Source health: ok", out.getvalue())

    def test_once_with_modbus_source_uses_adapter_configuration(self):
        out = StringIO()
        with mock.patch("telemetry.sources.modbus.ModbusTCPAdapter", _FakeModbusAdapter):
            call_command(
                "ingest_telemetry",
                "--source",
                "modbus",
                "--once",
                "--modbus-host",
                "plc.local",
                "--modbus-port",
                "1502",
                "--modbus-unit",
                "7",
                "--modbus-timeout",
                "0.25",
                stdout=out,
            )

        self.assertGreaterEqual(len(_FakeModbusAdapter.instances), 1)
        adapter = _FakeModbusAdapter.instances[-1]
        self.assertEqual(adapter._host, "plc.local")
        self.assertEqual(adapter._port, 1502)
        self.assertEqual(adapter._unit_id, 7)
        self.assertAlmostEqual(adapter._timeout, 0.25)
        self.assertTrue(adapter.closed)
        self.assertEqual(TelemetryReading.objects.count(), 1)
        reading = TelemetryReading.objects.get(sensor=self.sensor_ph)
        self.assertEqual(reading.status, "NORMAL")
        self.assertEqual(reading.source, "modbus:plc.local:1502")
        self.assertIn("Source health: connected", out.getvalue())


class SourceHealthEndpointTest(TestCase):
    def test_returns_status_for_simulator_and_modbus(self):
        resp = self.client.get("/api/health/sources/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("simulator", data)
        self.assertIn("modbus", data)
        self.assertEqual(data["simulator"]["name"], "simulator:seed=42")
        self.assertEqual(data["simulator"]["status"], "ok")
        self.assertIn(data["modbus"]["status"], {"disconnected", "unavailable"})
