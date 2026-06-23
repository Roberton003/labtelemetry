-- Sensores com alerta ativo e recência do alerta
-- Útil para: operação — quais sensores precisam de atenção agora

SELECT
    s.name AS sensor,
    s.parameter,
    s.operational_status,
    a.message,
    a.created_at AS alerta_desde,
    ROUND(EXTRACT(EPOCH FROM (NOW() - a.created_at)) / 60, 0) AS minutos_ativo
FROM telemetry_telemetrysensor s
JOIN telemetry_telemetryalert a ON a.sensor_id = s.id
WHERE a.is_active = TRUE
ORDER BY a.created_at DESC;
