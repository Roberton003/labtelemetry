from django.contrib import admin
from .models import TelemetrySensor, TelemetryReading, TelemetryAlert

@admin.register(TelemetrySensor)
class TelemetrySensorAdmin(admin.ModelAdmin):
    list_display = ("name", "parameter", "status", "calibration_factor", "created_at")
    list_filter = ("parameter", "status")
    search_fields = ("name",)

@admin.register(TelemetryReading)
class TelemetryReadingAdmin(admin.ModelAdmin):
    list_display = ("sensor", "timestamp", "raw_value", "calibrated_value", "status")
    list_filter = ("status", "sensor")
    date_hierarchy = "timestamp"

@admin.register(TelemetryAlert)
class TelemetryAlertAdmin(admin.ModelAdmin):
    list_display = ("sensor", "message", "is_active", "timestamp", "resolved_at")
    list_filter = ("is_active", "sensor")
    search_fields = ("message",)
