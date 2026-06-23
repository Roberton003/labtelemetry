from datetime import datetime, timezone

from django.test import TestCase
from django.utils import timezone as tz

from telemetry.models import TelemetryAlert, TelemetryReading, TelemetrySensor
from telemetry.quality import DRIFT_THRESHOLD, THRESHOLDS, evaluate_and_alert, evaluate_reading


class TelemetrySensorModelTest(TestCase):
    def test_str_representation(self):
        sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")
        expected = f"{sensor.name} ({sensor.get_parameter_display()})"
        self.assertEqual(str(sensor), expected)

    def test_default_status(self):
        sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")
        self.assertEqual(sensor.status, "HEALTHY")

    def test_default_calibration_factor(self):
        sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")
        self.assertEqual(sensor.calibration_factor, 1.0)


class TelemetryReadingModelTest(TestCase):
    def setUp(self):
        self.sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")

    def test_str_representation(self):
        now = tz.now()
        reading = TelemetryReading.objects.create(
            sensor=self.sensor, timestamp=now, raw_value=7.0, calibrated_value=7.0
        )
        expected = f"{self.sensor.name} - {now} - {reading.calibrated_value}"
        self.assertEqual(str(reading), expected)

    def test_default_status(self):
        reading = TelemetryReading.objects.create(
            sensor=self.sensor, timestamp=tz.now(), raw_value=7.0, calibrated_value=7.0
        )
        self.assertEqual(reading.status, "NORMAL")

    def test_sensor_reading_relationship(self):
        reading = TelemetryReading.objects.create(
            sensor=self.sensor, timestamp=tz.now(), raw_value=7.0, calibrated_value=7.0
        )
        self.assertIn(reading, self.sensor.readings.all())


class TelemetryAlertModelTest(TestCase):
    def setUp(self):
        self.sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")

    def test_str_active(self):
        alert = TelemetryAlert.objects.create(sensor=self.sensor, message="Alerta de teste")
        self.assertIn("ATIVO", str(alert))

    def test_str_resolved(self):
        alert = TelemetryAlert.objects.create(
            sensor=self.sensor, message="Alerta resolvido", is_active=False
        )
        self.assertIn("RESOLVIDO", str(alert))

    def test_default_active(self):
        alert = TelemetryAlert.objects.create(sensor=self.sensor, message="Teste")
        self.assertTrue(alert.is_active)

    def test_default_resolved_at(self):
        alert = TelemetryAlert.objects.create(sensor=self.sensor, message="Teste")
        self.assertIsNone(alert.resolved_at)


class QualityGatesTest(TestCase):
    def setUp(self):
        self.sensor_ph = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")
        self.sensor_turb = TelemetrySensor.objects.create(name="Sensor Turbidez", parameter="TURBIDITY")
        self.sensor_toc = TelemetrySensor.objects.create(name="Sensor TOC", parameter="TOC")

    def _reading(self, sensor, calibrated, raw=None):
        return TelemetryReading(
            sensor=sensor,
            timestamp=tz.now(),
            raw_value=raw if raw is not None else calibrated,
            calibrated_value=calibrated,
        )

    def test_normal_within_bounds_ph(self):
        reading = self._reading(self.sensor_ph, 7.2)
        self.assertEqual(evaluate_reading(reading), "NORMAL")

    def test_normal_boundary_ph_min(self):
        reading = self._reading(self.sensor_ph, 6.0)
        self.assertEqual(evaluate_reading(reading), "NORMAL")

    def test_normal_boundary_ph_max(self):
        reading = self._reading(self.sensor_ph, 8.5)
        self.assertEqual(evaluate_reading(reading), "NORMAL")

    def test_out_of_bounds_ph_high(self):
        reading = self._reading(self.sensor_ph, 9.0)
        self.assertEqual(evaluate_reading(reading), "OUT_OF_BOUNDS")

    def test_out_of_bounds_ph_low(self):
        reading = self._reading(self.sensor_ph, 5.5)
        self.assertEqual(evaluate_reading(reading), "OUT_OF_BOUNDS")

    def test_normal_turbidity(self):
        reading = self._reading(self.sensor_turb, 3.0)
        self.assertEqual(evaluate_reading(reading), "NORMAL")

    def test_out_of_bounds_turbidity(self):
        reading = self._reading(self.sensor_turb, 6.0)
        self.assertEqual(evaluate_reading(reading), "OUT_OF_BOUNDS")

    def test_normal_toc(self):
        reading = self._reading(self.sensor_toc, 5.0)
        self.assertEqual(evaluate_reading(reading), "NORMAL")

    def test_out_of_bounds_toc(self):
        reading = self._reading(self.sensor_toc, 12.0)
        self.assertEqual(evaluate_reading(reading), "OUT_OF_BOUNDS")

    def test_drift_warning(self):
        reading = self._reading(self.sensor_ph, 7.2, raw=6.0)
        drift = abs(7.2 - 6.0) / 6.0
        self.assertGreater(drift, DRIFT_THRESHOLD)
        self.assertEqual(evaluate_reading(reading), "DRIFT_WARNING")

    def test_no_drift_when_within_threshold(self):
        reading = self._reading(self.sensor_ph, 7.05, raw=7.0)
        self.assertEqual(evaluate_reading(reading), "NORMAL")

    def test_evaluate_and_alert_creates_alert(self):
        reading = TelemetryReading.objects.create(
            sensor=self.sensor_ph, timestamp=tz.now(), raw_value=7.0, calibrated_value=9.0
        )
        evaluate_and_alert(reading)
        self.assertTrue(TelemetryAlert.objects.filter(sensor=self.sensor_ph, is_active=True).exists())

    def test_evaluate_and_alert_no_duplicate(self):
        reading = TelemetryReading.objects.create(
            sensor=self.sensor_ph, timestamp=tz.now(), raw_value=7.0, calibrated_value=9.0
        )
        evaluate_and_alert(reading)
        evaluate_and_alert(reading)
        self.assertEqual(
            TelemetryAlert.objects.filter(sensor=self.sensor_ph, is_active=True).count(), 1
        )

    def test_evaluate_and_alert_normal_no_alert(self):
        reading = TelemetryReading.objects.create(
            sensor=self.sensor_ph, timestamp=tz.now(), raw_value=7.0, calibrated_value=7.0
        )
        evaluate_and_alert(reading)
        self.assertFalse(TelemetryAlert.objects.filter(sensor=self.sensor_ph).exists())

    def test_unknown_parameter_is_normal(self):
        sensor_unknown = TelemetrySensor.objects.create(name="Sensor X", parameter="UNKNOWN")
        reading = self._reading(sensor_unknown, 999.0)
        self.assertEqual(evaluate_reading(reading), "NORMAL")


class SimulateTelemetryCommandTest(TestCase):
    def test_once_creates_readings_and_sensors(self):
        out = self._capture_command(once=True, sensors=6)
        self.assertIn("Geradas", out)
        self.assertGreater(TelemetryReading.objects.count(), 0)

    def test_seed_reproducibility(self):
        self._capture_command(once=True, sensors=6, seed=42)
        r1 = list(TelemetryReading.objects.all().values_list("raw_value", "calibrated_value").order_by("sensor_id", "timestamp"))
        TelemetryReading.objects.all().delete()
        TelemetryAlert.objects.all().delete()
        TelemetrySensor.objects.all().delete()
        self._capture_command(once=True, sensors=6, seed=42)
        r2 = list(TelemetryReading.objects.all().values_list("raw_value", "calibrated_value").order_by("sensor_id", "timestamp"))
        self.assertEqual(r1, r2)

    def test_anomaly_rate_100_percent(self):
        out = self._capture_command(once=True, sensors=6, anomaly_rate=1.0)
        self.assertGreater(TelemetryReading.objects.count(), 0)

    def test_no_sensors_shows_error(self):
        out = self._capture_command(once=True, sensors=0)
        self.assertIn("Nenhum sensor", out)

    def _capture_command(self, once, sensors, seed=None, anomaly_rate=0.1):
        from io import StringIO
        from django.core.management import call_command
        buf = StringIO()
        err = StringIO()
        args = ["--once"] if once else []
        if sensors:
            args.extend(["--sensors", str(sensors)])
        if seed is not None:
            args.extend(["--seed", str(seed)])
        args.extend(["--anomaly-rate", str(anomaly_rate)])
        call_command("simulate_telemetry", *args, stdout=buf, stderr=err)
        return buf.getvalue() + err.getvalue()


class ApiEndpointTest(TestCase):
    def setUp(self):
        self.sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")
        TelemetryReading.objects.create(
            sensor=self.sensor, timestamp=tz.now(), raw_value=7.0, calibrated_value=7.2
        )
        TelemetryAlert.objects.create(sensor=self.sensor, message="Test alert")

    def test_sensor_list_returns_json(self):
        resp = self.client.get("/api/sensors/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/json")
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_readings_recent_returns_json(self):
        resp = self.client.get("/api/readings/recent/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("parameter", data[0])
        self.assertIn("value", data[0])

    def test_readings_recent_respects_limit(self):
        resp = self.client.get("/api/readings/recent/?limit=1")
        self.assertEqual(len(resp.json()), 1)

    def test_sensor_readings_returns_json(self):
        resp = self.client.get(f"/api/sensors/{self.sensor.id}/readings/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_alerts_active_returns_json(self):
        resp = self.client.get("/api/alerts/active/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_alerts_active_filters_resolved(self):
        TelemetryAlert.objects.create(sensor=self.sensor, message="Resolved", is_active=False)
        resp = self.client.get("/api/alerts/active/")
        self.assertEqual(len(resp.json()), 1)

    def test_summary_returns_json(self):
        resp = self.client.get("/api/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_sensors", data)
        self.assertIn("total_readings", data)
        self.assertIn("active_alerts", data)

    def test_ordering_by_timestamp(self):
        resp = self.client.get("/api/readings/recent/")
        data = resp.json()
        if len(data) > 1:
            timestamps = [r["timestamp"] for r in data]
            self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_source_health_returns_json(self):
        resp = self.client.get("/api/health/sources/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("simulator", data)
        self.assertIn("modbus", data)
        self.assertIn("status", data["simulator"])
        self.assertIn("status", data["modbus"])

    def test_dashboard_renders(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"LabTelemetry", resp.content)

    def test_dashboard_cards_renders(self):
        resp = self.client.get("/dashboard/cards/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sensores", resp.content)

    def test_dashboard_readings_renders(self):
        resp = self.client.get("/dashboard/readings/")
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_alerts_renders(self):
        resp = self.client.get("/dashboard/alerts/")
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_sensors_renders(self):
        resp = self.client.get("/dashboard/sensors/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sensor pH", resp.content)

    def test_dashboard_source_health_renders(self):
        resp = self.client.get("/dashboard/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Simulator", resp.content)
        self.assertIn(b"Modbus", resp.content)


class ThresholdConfigTest(TestCase):
    def test_ph_threshold_exists(self):
        t = THRESHOLDS.get("PH")
        self.assertIsNotNone(t)
        self.assertEqual(t.min_value, 6.0)
        self.assertEqual(t.max_value, 8.5)

    def test_turbidity_threshold_exists(self):
        t = THRESHOLDS.get("TURBIDITY")
        self.assertIsNotNone(t)
        self.assertIsNone(t.min_value)
        self.assertEqual(t.max_value, 5.0)

    def test_toc_threshold_exists(self):
        t = THRESHOLDS.get("TOC")
        self.assertIsNotNone(t)
        self.assertIsNone(t.min_value)
        self.assertEqual(t.max_value, 10.0)


class EndToEndTest(TestCase):
    """Fase 8: Simular → API → Dashboard — fluxo completo."""

    def test_simulate_to_api_to_dashboard(self):
        from io import StringIO
        from django.core.management import call_command

        # 1. Executa simulador com --once e seed fixo
        buf = StringIO()
        call_command(
            "simulate_telemetry", "--once", "--sensors", "6",
            "--seed", "42", "--anomaly-rate", "0.2",
            stdout=buf,
        )
        output = buf.getvalue()
        self.assertIn("Geradas", output)
        reading_count = TelemetryReading.objects.count()
        self.assertGreater(reading_count, 0, "Simulador deveria gerar readings")

        # 2. Summary API confere totais
        resp = self.client.get("/api/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_sensors"], 6)
        self.assertEqual(data["total_readings"], reading_count)
        self.assertIsNotNone(data["last_reading_timestamp"])

        # 3. Sensor list via API
        resp = self.client.get("/api/sensors/")
        self.assertEqual(resp.status_code, 200)
        sensors = resp.json()
        self.assertEqual(len(sensors), 6)
        params = {s["parameter"] for s in sensors}
        self.assertIn("PH", params)
        self.assertIn("TURBIDITY", params)
        self.assertIn("TOC", params)

        # 4. Dashboard cards rendering
        resp = self.client.get("/dashboard/cards/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, str(reading_count))
        self.assertContains(resp, "6")

        # 5. Dashboard readings rendering
        resp = self.client.get("/dashboard/readings/")
        self.assertEqual(resp.status_code, 200)

        # 6. Dashboard alerts rendering (pode ter alertas com anomaly_rate 0.2)
        resp = self.client.get("/dashboard/alerts/")
        self.assertEqual(resp.status_code, 200)

        # 7. Dashboard main page
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "LabTelemetry")

    def test_e2e_without_anomaly_no_alerts(self):
        """Simulador sem anomalias não gera alertas."""
        from io import StringIO
        from django.core.management import call_command

        buf = StringIO()
        call_command(
            "simulate_telemetry", "--once", "--sensors", "3",
            "--seed", "1", "--anomaly-rate", "0.0",
            stdout=buf,
        )
        # Nenhum alerta deve existir
        self.assertEqual(TelemetryAlert.objects.count(), 0)
        readings = TelemetryReading.objects.count()
        self.assertGreater(readings, 0)

        # Summary reflete dados sem alertas
        resp = self.client.get("/api/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_readings"], readings)
        self.assertEqual(data["active_alerts"], 0)


class DeprecatedRoutesReturn404Test(TestCase):
    """NC-008: Old bare API routes must return 404 after /api/ migration."""

    def setUp(self):
        self.sensor = TelemetrySensor.objects.create(name="Sensor pH", parameter="PH")

    def test_old_sensors_returns_404(self):
        resp = self.client.get("/sensors/")
        self.assertEqual(resp.status_code, 404)

    def test_old_readings_recent_returns_404(self):
        resp = self.client.get("/readings/recent/")
        self.assertEqual(resp.status_code, 404)

    def test_old_summary_returns_404(self):
        resp = self.client.get("/summary/")
        self.assertEqual(resp.status_code, 404)

    def test_old_sensor_readings_returns_404(self):
        resp = self.client.get(f"/sensors/{self.sensor.id}/readings/")
        self.assertEqual(resp.status_code, 404)

    def test_old_alerts_active_returns_404(self):
        resp = self.client.get("/alerts/active/")
        self.assertEqual(resp.status_code, 404)


class TelemetrySimulateAliasCommandTest(TestCase):
    def test_alias_accepts_count_and_seed(self):
        from io import StringIO
        from django.core.management import call_command

        buf = StringIO()
        call_command(
            "telemetry_simulate",
            "--sensors",
            "2",
            "--count",
            "3",
            "--seed",
            "42",
            stdout=buf,
        )

        self.assertIn("Geradas", buf.getvalue())
        self.assertEqual(TelemetrySensor.objects.count(), 6)
        self.assertEqual(TelemetryReading.objects.count(), 18)
