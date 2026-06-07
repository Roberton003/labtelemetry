from django.db import models

class TelemetrySensor(models.Model):
    PARAMETER_CHOICES = [
        ("PH", "Potencial Hidrogeniônico"),
        ("TURBIDITY", "Turbidez (NTU)"),
        ("TOC", "Carbono Orgânico Total"),
    ]
    STATUS_CHOICES = [
        ("HEALTHY", "Saudável"),
        ("DRIFTING", "Desvio Detectado (Drift)"),
        ("FAILED", "Falha de Sinal"),
    ]
    name = models.CharField(max_length=100)
    parameter = models.CharField(max_length=20, choices=PARAMETER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="HEALTHY")
    calibration_factor = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_parameter_display()})"

class TelemetryReading(models.Model):
    STATUS_CHOICES = [
        ("NORMAL", "Normal"),
        ("OUT_OF_BOUNDS", "Fora dos Limites de Processo"),
        ("DRIFT_WARNING", "Alerta de Desvio de Calibração"),
    ]
    sensor = models.ForeignKey(TelemetrySensor, on_delete=models.CASCADE, related_name="readings")
    timestamp = models.DateTimeField()
    raw_value = models.FloatField()
    calibrated_value = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NORMAL")

    def __str__(self):
        return f"{self.sensor.name} - {self.timestamp} - {self.calibrated_value}"

class TelemetryAlert(models.Model):
    sensor = models.ForeignKey(TelemetrySensor, on_delete=models.CASCADE, related_name="alerts")
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status_str = "ATIVO" if self.is_active else "RESOLVIDO"
        return f"ALERTA [{status_str}] - {self.sensor.name}: {self.message[:30]}"
