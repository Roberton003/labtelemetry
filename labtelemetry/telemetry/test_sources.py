from datetime import datetime, timezone

from django.test import TestCase

from telemetry.sources.base import TelemetrySample
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
