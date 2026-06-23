-- Últimas 50 leituras com status e alerta associado (se houver)
-- Útil para: auditoria rápida do estado atual do sistema

SELECT
    r.id,
    s.name AS sensor,
    r.parameter,
    r.calibrated_value,
    r.timestamp,
    r.status,
    r.is_anomaly,
    a.message AS alerta_ativo
FROM telemetry_telemetryreading r
JOIN telemetry_telemetrysensor s ON s.id = r.sensor_id
LEFT JOIN telemetry_telemetryalert a
    ON a.sensor_id = r.sensor_id
    AND a.is_active = TRUE
    AND a.created_at >= r.timestamp
ORDER BY r.timestamp DESC
LIMIT 50;
