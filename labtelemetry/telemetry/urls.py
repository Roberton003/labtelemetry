from django.urls import path

from telemetry import views

urlpatterns = [
    # Dashboard HTML (raiz)
    path("", views.dashboard, name="dashboard"),
    # Dashboard partials HTMX
    path("dashboard/cards/", views.dashboard_cards, name="dashboard-cards"),
    path("dashboard/readings/", views.dashboard_readings, name="dashboard-readings"),
    path("dashboard/alerts/", views.dashboard_alerts, name="dashboard-alerts"),
    path("dashboard/sensors/", views.dashboard_sensors, name="dashboard-sensors"),
    # API REST JSON (prefixo /api/ conforme Plano 001)
    path("api/sensors/", views.sensor_list, name="sensor-list"),
    path("api/readings/recent/", views.readings_recent, name="readings-recent"),
    path("api/sensors/<int:sensor_id>/readings/", views.sensor_readings, name="sensor-readings"),
    path("api/alerts/active/", views.alerts_active, name="alerts-active"),
    path("api/summary/", views.summary, name="summary"),
]
