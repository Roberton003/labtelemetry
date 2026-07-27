from dataclasses import dataclass

from telemetry.models import TelemetryAlert, TelemetryReading


@dataclass
class Threshold:
    param: str
    min_value: float | None
    max_value: float | None


THRESHOLDS: dict[str, Threshold] = {
    "PH": Threshold("PH", 6.0, 8.5),
    "TURBIDITY": Threshold("TURBIDITY", None, 5.0),
    "TOC": Threshold("TOC", None, 10.0),
}

DRIFT_THRESHOLD = 0.1


def evaluate_reading(reading: TelemetryReading) -> str:
    threshold = THRESHOLDS.get(reading.sensor.parameter)
    if threshold is None:
        return "NORMAL"

    value = reading.calibrated_value

    if threshold.min_value is not None and value < threshold.min_value:
        return "OUT_OF_BOUNDS"
    if threshold.max_value is not None and value > threshold.max_value:
        return "OUT_OF_BOUNDS"

    drift = abs(value - reading.raw_value) / max(abs(reading.raw_value), 0.001)
    if drift > DRIFT_THRESHOLD:
        return "DRIFT_WARNING"

    return "NORMAL"


def raise_alert(reading: TelemetryReading) -> None:
    """Abre um alerta para a leitura, se ainda nao houver um ativo do mesmo tipo.

    Idempotente: chamar duas vezes para o mesmo sensor/status nao duplica o
    alerta. Nao toca na leitura — quem persiste e o chamador.
    """
    status = reading.status
    if status not in ("OUT_OF_BOUNDS", "DRIFT_WARNING"):
        return

    existing_active = TelemetryAlert.objects.filter(
        sensor=reading.sensor,
        is_active=True,
        message__startswith=f"[{status}]",
    ).exists()
    if not existing_active:
        TelemetryAlert.objects.create(
            sensor=reading.sensor,
            message=f"[{status}] {reading.sensor.parameter}={reading.calibrated_value:.2f} em {reading.timestamp.isoformat()}",
        )


def evaluate_and_alert(reading: TelemetryReading) -> str:
    """Avalia, persiste e alerta uma leitura isolada.

    Para lotes, prefira `evaluate_reading` + `bulk_create` + `raise_alert`:
    esta funcao faz um INSERT/UPDATE por leitura.
    """
    reading.status = evaluate_reading(reading)
    if reading.pk is None:
        reading.save()
    else:
        reading.save(update_fields=["status"])

    raise_alert(reading)

    return reading.status
