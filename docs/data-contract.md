# Data Contract - LabTelemetry API

## Escopo

Este contrato cobre o schema e a semantica dos dados expostos pela API JSON
publica do LabTelemetry.

## Produtores e Consumidores

| Papel | Sistema | Dado |
|---|---|---|
| Produtor primario | `telemetry_simulate` ou `ingest_telemetry` | `TelemetryReading` |
| Produtor secundario | `quality.py` | `TelemetryAlert` |
| Consumidor | Dashboard HTML/HTMX | `/api/summary/`, `/api/readings/recent/`, `/api/alerts/active/` |
| Consumidor | Avaliador tecnico | `curl` ou cliente HTTP simples |

## Schemas

### `TelemetryReading` em `/api/readings/recent/`

```json
{
  "id": 1,
  "sensor_id": 1,
  "sensor_name": "Sensor pH #1",
  "parameter": "PH",
  "timestamp": "2026-06-22T10:30:00Z",
  "raw_value": 7.05,
  "calibrated_value": 7.05,
  "value": 7.05,
  "source": "simulator:seed=42",
  "status": "NORMAL"
}
```

Contrato:

- `sensor_id`: FK para `TelemetrySensor`
- `sensor_name`: nome legivel do sensor
- `parameter`: enum `PH | TURBIDITY | TOC`
- `raw_value`: valor lido da fonte
- `calibrated_value`: valor persistido para avaliacao de qualidade
- `value`: alias de `calibrated_value` no endpoint de leituras recentes
- `source`: lineage curto, por exemplo `simulator:seed=42` ou `modbus:host:port`
- `status`: enum `NORMAL | OUT_OF_BOUNDS | DRIFT_WARNING`

### `TelemetryReading` em `/api/sensors/{id}/readings/`

```json
{
  "id": 1,
  "timestamp": "2026-06-22T10:30:00Z",
  "raw_value": 7.05,
  "calibrated_value": 7.05,
  "source": "simulator:seed=42",
  "status": "NORMAL"
}
```

### `TelemetrySensor`

```json
{
  "id": 1,
  "name": "Sensor pH #1",
  "parameter": "PH",
  "status": "HEALTHY",
  "calibration_factor": 1.0
}
```

### `TelemetryAlert`

```json
{
  "id": 1,
  "sensor_id": 1,
  "sensor_name": "Sensor pH #1",
  "message": "PH fora do limite: 9.20",
  "timestamp": "2026-06-22T10:30:05Z"
}
```

## Endpoints

| Endpoint | Metodo | Retorno |
|---|---|---|
| `/api/sensors/` | GET | Lista de sensores |
| `/api/readings/recent/?limit=50` | GET | Leituras recentes agregadas |
| `/api/sensors/{id}/readings/?limit=100` | GET | Leituras de um sensor |
| `/api/alerts/active/` | GET | Alertas ativos |
| `/api/summary/` | GET | Resumo operacional |
| `/api/health/sources/` | GET | Estado das fontes por nome |

## Regras De Qualidade

| Regra | Descricao | Efeito |
|---|---|---|
| Limite inferior | `calibrated_value < lower_threshold` | `OUT_OF_BOUNDS` |
| Limite superior | `calibrated_value > upper_threshold` | `OUT_OF_BOUNDS` |
| Drift | Divergencia relevante entre `raw_value` e `calibrated_value` | `DRIFT_WARNING` |
| Alerta duplicado | Ja existe alerta ativo equivalente | Nao cria duplicata |

## Garantias e Limitacoes

- `ingest_telemetry --once` nao faz deduplicacao; cada execucao cria novas leituras.
- Cada leitura e persistida individualmente; nao existe batch atomico publico.
- `source` guarda somente lineage curto, nao payload bruto do protocolo.
- Nao ha SLO publico de latencia para a API.

## Versionamento

Contrato atual: `v1`.

Mudancas incompatíveis exigem:

1. migration reversivel;
2. atualizacao desta documentacao;
3. ajuste dos testes de API e ingestao.
