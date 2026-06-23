# Data Contract — LabTelemetry API

## Escopo

Este contrato cobre o schema e semântica dos dados expostos pela API REST
do LabTelemetry e armazenados no banco PostgreSQL/SQLite.

## Produtores e Consumidores

| Papel | Sistema | Dado |
|-------|---------|------|
| **Produtor primário** | Simulador (`telemetry_simulate`) ou fonte OT (Modbus) | `TelemetryReading` |
| **Produtor secundário** | Quality gates (`quality.py`) | `TelemetryAlert` |
| **Consumidor** | Dashboard HTML (HTMX) | `GET /api/summary/`, `GET /api/sensors/`, etc. |
| **Consumidor** | Avaliador de portfólio | `curl` direto nos endpoints |

## Schemas

### `TelemetryReading` (entrada pelo produtor)

```json
{
  "id": 1,
  "sensor": "Sensor pH #1",
  "sensor_id": 1,
  "parameter": "PH",
  "value": 7.05,
  "timestamp": "2026-06-22T10:30:00Z",
  "unit": "",
  "status": "NORMAL"
}
```

**Contrato:**
- `id`: BigAutoField, gerado pelo banco
- `sensor`: string, nome legível do sensor
- `sensor_id`: int, FK para TelemetrySensor
- `parameter`: string, enum `PH | TURBIDITY | TOC`
- `value`: float — `calibrated_value` após fator de calibração
- `timestamp`: string ISO 8601 com timezone (UTC)
- `unit`: string, vazio por simplicidade
- `status`: string, enum `NORMAL | OUT_OF_BOUNDS | DRIFT_WARNING`

### `TelemetrySensor`

```json
{
  "id": 1,
  "name": "Sensor pH #1",
  "parameter": "PH",
  "unit": "",
  "operational_status": "HEALTHY",
  "is_active": true
}
```

### `TelemetryAlert`

```json
{
  "id": 1,
  "sensor": "Sensor pH #1",
  "sensor_id": 1,
  "message": "PH fora do limite: 9.20",
  "is_active": true,
  "created_at": "2026-06-22T10:30:05Z"
}
```

## Endpoints e Contratos

| Endpoint | Método | Retorno | Contrato |
|----------|--------|---------|----------|
| `/api/sensors/` | GET | Lista de sensores | Array de TelemetrySensor |
| `/api/readings/recent/` | GET | Últimas 50 leituras | Array de TelemetryReading |
| `/api/sensors/{id}/readings/` | GET | Leituras de um sensor | Array de TelemetryReading |
| `/api/alerts/active/` | GET | Alertas ativos | Array de TelemetryAlert |
| `/api/summary/` | GET | Resumo | `{total_sensors, total_readings, active_alerts, ...}` |
| `/api/health/sources/` | GET | Saúde das fontes | Array de `{name, status, last_read, age_seconds}` |

## Regras de Qualidade

| Regra | Descrição | Ação |
|-------|-----------|------|
| Limite inferior | `value < lower_threshold` | Status `OUT_OF_BOUNDS`, alerta criado |
| Limite superior | `value > upper_threshold` | Status `OUT_OF_BOUNDS`, alerta criado |
| Drift | Média móvel (5) desvia > 1.5σ da média histórica | Status `DRIFT_WARNING`, alerta criado |
| Alerta duplicado | Se alerta ativo já existe para o mesmo problema | Ignorado (sem duplicação) |

## Garantias e Limitações

- **Idempotência:** O comando `ingest_telemetry --once` não deduplica —
  cada execução cria novas leituras. A idempotência é manual (controle
  via seed + timestamp).
- **Consistência:** Cada leitura é inserida em transação individual.
  Não há garantia de batch atômico.
- **Disponibilidade:** Sem replica ou HA — o banco é single-node local.
- **Latência:** < 50ms para leituras em SQLite local; < 10ms em PostgreSQL.

## Versionamento

Este contrato é versão 1 (MVP). Mudanças incompatíveis exigem:
1. ADR documentando a mudança
2. Migration com rollback
3. Atualização deste contrato
