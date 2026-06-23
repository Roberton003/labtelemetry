-- Freshness por sensor: há quanto tempo cada sensor não envia leitura
-- Útil para: detectar fontes que pararam de enviar dados

SELECT
    s.name AS sensor,
    s.parameter,
    s.operational_status,
    MAX(r.timestamp) AS ultima_leitura,
    ROUND(EXTRACT(EPOCH FROM (NOW() - MAX(r.timestamp))) / 60, 0) AS minutos_sem_dados,
    CASE
        WHEN MAX(r.timestamp) IS NULL THEN 'sem_leituras'
        WHEN NOW() - MAX(r.timestamp) > INTERVAL '10 minutes' THEN 'stale'
        ELSE 'fresh'
    END AS status_freshness
FROM telemetry_telemetrysensor s
LEFT JOIN telemetry_telemetryreading r ON r.sensor_id = s.id
GROUP BY s.id, s.name, s.parameter, s.operational_status
ORDER BY ultima_leitura DESC NULLS LAST;
