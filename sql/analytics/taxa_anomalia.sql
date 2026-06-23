-- Taxa de anomalia por sensor
-- Útil para: identificar sensores com maior incidência de leituras fora dos limites

SELECT
    s.name AS sensor,
    s.parameter,
    COUNT(r.id) AS total_leituras,
    COUNT(r.id) FILTER (WHERE r.is_anomaly = TRUE) AS anomalias,
    ROUND(
        100.0 * COUNT(r.id) FILTER (WHERE r.is_anomaly = TRUE) / NULLIF(COUNT(r.id), 0),
        2
    ) AS taxa_anomalia_pct
FROM telemetry_telemetrysensor s
LEFT JOIN telemetry_telemetryreading r ON r.sensor_id = s.id
GROUP BY s.id, s.name, s.parameter
ORDER BY taxa_anomalia_pct DESC NULLS LAST;
