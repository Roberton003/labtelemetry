# Data Model - LabTelemetry

## Grao Fundamental: `TelemetryReading`

Cada linha representa uma leitura pontual de um sensor em um instante,
persistida apos ingestao e avaliada pelas regras de qualidade do backend.

| Campo | Tipo | Semantica | Exemplo |
|---|---|---|---|
| `id` | `BigAutoField` | Identificador unico da leitura | `1` |
| `sensor` | `ForeignKey(TelemetrySensor)` | Sensor associado a leitura | `Sensor pH #1` |
| `sensor_id` | `int` | FK para `TelemetrySensor` | `42` |
| `timestamp` | `DateTimeField` | Instante da coleta, timezone-aware | `2026-06-22T10:30:00Z` |
| `raw_value` | `FloatField` | Valor recebido da fonte | `7.02` |
| `calibrated_value` | `FloatField` | Valor persistido para avaliacao | `7.02` |
| `source` | `CharField(100)` | Origem logica da leitura | `simulator:seed=42` |
| `status` | `CharField(20)` | Resultado da regra de qualidade | `NORMAL` |

### Indices

- Composto: `(sensor_id, timestamp)` para consultas por sensor e janela temporal.

## Entidades Suporte

### `TelemetrySensor`

| Campo | Tipo | Exemplo |
|---|---|---|
| `name` | `CharField(100)` | `Sensor pH #1` |
| `parameter` | `CharField(20)` | `PH` |
| `status` | `CharField(20)` | `HEALTHY` |
| `calibration_factor` | `FloatField(default=1.0)` | `1.05` |
| `created_at` | `DateTimeField(auto_now_add=True)` | `2026-06-22T10:30:05Z` |

### `TelemetryAlert`

| Campo | Tipo | Exemplo |
|---|---|---|
| `sensor` | `ForeignKey(TelemetrySensor)` | `Sensor pH #1` |
| `message` | `TextField` | `PH fora do limite: 9.20` |
| `is_active` | `BooleanField(default=True)` | `True` |
| `timestamp` | `DateTimeField(auto_now_add=True)` | `2026-06-22T10:30:05Z` |
| `resolved_at` | `DateTimeField(null=True, blank=True)` | `null` |

## Faixas Validas

Os thresholds atuais sao premissas do laboratorio e vivem em
`telemetry/quality.py`.

| Parametro | Limite Inferior | Limite Superior | Unidade |
|---|---|---|---|
| pH | 6.0 | 8.5 | adimensional |
| Turbidez | 0.0 | 5.0 | NTU (simulado) |
| TOC | 0.0 | 10.0 | mg/L (simulado) |

## Relacionamentos

```text
TelemetrySensor 1--N TelemetryReading
TelemetrySensor 1--N TelemetryAlert
```

## Notas Tecnicas

- Timestamps sao armazenados em UTC com `USE_TZ=True`.
- `source` preserva lineage curto da ingestao, mas nao persiste payload bruto do protocolo.
- O backend atual persiste `raw_value` e `calibrated_value` com o mesmo valor no fluxo de ingestao unificado.
- Nao ha soft delete nas entidades principais.
