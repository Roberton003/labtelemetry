-- Volume de leituras por janela temporal e parâmetro
-- Útil para: entender padrão de ingestão, detectar gaps

SELECT
    date_trunc('hour', timestamp) AS janela_hora,
    parameter,
    COUNT(*) AS total_leituras,
    ROUND(AVG(calibrated_value), 2) AS valor_medio
FROM telemetry_telemetryreading
GROUP BY janela_hora, parameter
ORDER BY janela_hora DESC, parameter;

-- Versão diária
SELECT
    date_trunc('day', timestamp) AS janela_dia,
    parameter,
    COUNT(*) AS total_leituras,
    ROUND(AVG(calibrated_value), 2) AS valor_medio,
    MIN(calibrated_value) AS valor_min,
    MAX(calibrated_value) AS valor_max
FROM telemetry_telemetryreading
GROUP BY janela_dia, parameter
ORDER BY janela_dia DESC, parameter;
