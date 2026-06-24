from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from telemetry.models import TelemetryAlert, TelemetryReading, TelemetrySensor
from telemetry.sources import ModbusTCPAdapter, SimulatorAdapter

# tracer para spans manuais (ex.: summary)
try:
    from opentelemetry import trace
    _tracer = trace.get_tracer(__name__)
except Exception:
    _tracer = None  # OTel desligado


def _json(data, status=200):
    return JsonResponse(data, encoder=DjangoJSONEncoder, status=status, safe=False)


def _source_health_payload() -> dict:
    sources = {
        "simulator": SimulatorAdapter().health(),
    }

    if ModbusTCPAdapter is None:
        sources["modbus"] = {
            "name": "modbus",
            "status": "unavailable",
            "last_read": None,
            "reason": "pymodbus not installed",
        }
    else:
        sources["modbus"] = ModbusTCPAdapter().health()

    return sources


@require_http_methods(["GET"])
def sensor_list(request):
    sensors = TelemetrySensor.objects.all().values("id", "name", "parameter", "status", "calibration_factor")
    return _json(list(sensors))


@require_http_methods(["GET"])
def readings_recent(request):
    limit = min(int(request.GET.get("limit", 50)), 500)
    readings = (
        TelemetryReading.objects.select_related("sensor")
        .order_by("-timestamp", "-id")[:limit]
    )
    data = [
        {
            "id": r.id,
            "sensor_id": r.sensor_id,
            "sensor_name": r.sensor.name,
            "parameter": r.sensor.parameter,
            "timestamp": r.timestamp,
            "raw_value": r.raw_value,
            "calibrated_value": r.calibrated_value,
            "value": r.calibrated_value,
            "source": r.source,
            "status": r.status,
        }
        for r in readings
    ]
    return _json(data)


@require_http_methods(["GET"])
def sensor_readings(request, sensor_id):
    limit = min(int(request.GET.get("limit", 100)), 500)
    readings = (
        TelemetryReading.objects.filter(sensor_id=sensor_id)
        .order_by("-timestamp", "-id")[:limit]
    )
    data = [
        {
            "id": r.id,
            "timestamp": r.timestamp,
            "raw_value": r.raw_value,
            "calibrated_value": r.calibrated_value,
            "source": r.source,
            "status": r.status,
        }
        for r in readings
    ]
    return _json(data)


@require_http_methods(["GET"])
def alerts_active(request):
    alerts = (
        TelemetryAlert.objects.filter(is_active=True)
        .select_related("sensor")
        .order_by("-timestamp")
    )
    data = [
        {
            "id": a.id,
            "sensor_id": a.sensor_id,
            "sensor_name": a.sensor.name,
            "message": a.message,
            "timestamp": a.timestamp,
        }
        for a in alerts
    ]
    return _json(data)


@require_http_methods(["GET"])
def dashboard(request):
    return render(request, "telemetry/dashboard.html")


@require_http_methods(["GET"])
def dashboard_cards(request):
    sensors = TelemetrySensor.objects.count()
    readings = TelemetryReading.objects.count()
    alerts = TelemetryAlert.objects.filter(is_active=True).count()
    last = TelemetryReading.objects.order_by("-timestamp").first()
    return render(request, "telemetry/_cards.html", {
        "total_sensors": sensors,
        "total_readings": readings,
        "active_alerts": alerts,
        "last_reading": last,
    })


@require_http_methods(["GET"])
def dashboard_readings(request):
    readings = TelemetryReading.objects.select_related("sensor").order_by("-timestamp", "-id")[:20]
    return render(request, "telemetry/_readings.html", {"readings": readings})


@require_http_methods(["GET"])
def dashboard_alerts(request):
    alerts = TelemetryAlert.objects.filter(is_active=True).select_related("sensor").order_by("-timestamp")
    return render(request, "telemetry/_alerts.html", {"alerts": alerts})


@require_http_methods(["GET"])
def dashboard_sensors(request):
    sensors = TelemetrySensor.objects.all()
    return render(request, "telemetry/_sensors.html", {"sensors": sensors})


@require_http_methods(["GET"])
def summary(request):
    if _tracer:
        with _tracer.start_as_current_span("summary") as span:
            span.set_attribute("endpoint", "summary")
            return _summary_data()
    return _summary_data()


@require_http_methods(["GET"])
def source_health(request):
    return _json(_source_health_payload())


@require_http_methods(["GET"])
def dashboard_source_health(request):
    sources = _source_health_payload()
    return render(request, "telemetry/_source_health.html", {"sources": sources.items()})


def _summary_data():
    total_sensors = TelemetrySensor.objects.count()
    total_readings = TelemetryReading.objects.count()
    active_alerts = TelemetryAlert.objects.filter(is_active=True).count()
    last_reading = TelemetryReading.objects.order_by("-timestamp", "-id").first()
    return _json({
        "total_sensors": total_sensors,
        "total_readings": total_readings,
        "active_alerts": active_alerts,
        "last_reading_timestamp": last_reading.timestamp if last_reading else None,
    })
