# Data Model — LabTelemetry

## Grão Fundamental: `TelemetryReading`

Cada linha representa **uma leitura pontual de um sensor em um instante**,
após calibração e classificação de qualidade.

| Campo | Tipo | Grão | Exemplo |
|-------|------|------|---------|
| `id` | `BigAutoField` | Identificador único da leitura | `1` |
| `sensor` | `ForeignKey(TelemetrySensor)` | Sensor que gerou a leitura | `Sensor pH #1` |
| `sensor_id` | `int` (FK) | FK para a tabela de sensores | `42` |
| `timestamp` | `DateTimeField` | Instante da coleta (timezone-aware) | `2026-06-22T10:30:00Z` |
| `raw_value` | `FloatField` | Valor lido diretamente do sensor/simulador | `7.02` |
| `calibrated_value` | `FloatField` | Valor após aplicar fator de calibração | `7.05` |
| `parameter` | `CharField(17)` | Parâmetro medido: `PH`, `TURBIDITY`, `TOC` | `PH` |
| `unit` | `CharField(20)` | Unidade de medida | `""` (adimensional por simplicidade) |
| `status` | `CharField(20)` | Qualidade: `NORMAL`, `OUT_OF_BOUNDS`, `DRIFT_WARNING` | `NORMAL` |
| `is_anomaly` | `BooleanField` | True se qualquer alerta foi disparado para esta leitura | `false` |

### Índices

- Composto: `(sensor_id, -timestamp)` — otimiza consultas "últimas N leituras por sensor"

## Entidades Suporte

### `TelemetrySensor`

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `name` | `CharField(100)` | `Sensor pH #1` |
| `parameter` | `CharField(17)` | `PH` |
| `unit` | `CharField(20)` | `""` |
| `calibration_factor` | `FloatField(default=1.0)` | `1.05` |
| `operational_status` | `CharField(20)` | `HEALTHY`, `DRIFTING`, `FAILED` |
| `is_active` | `BooleanField(default=True)` | `True` |

### `TelemetryAlert`

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `sensor` | `ForeignKey(TelemetrySensor)` | Sensor pH #1 |
| `message` | `TextField` | `PH fora do limite: 9.20` |
| `is_active` | `BooleanField(default=True)` | `True` |
| `created_at` | `DateTimeField(auto_now_add=True)` | `2026-06-22T10:30:05Z` |

## Faixas Válidas (Premissas de Laboratório)

Os thresholds foram definidos como premissas para simulação sintética e não
representam valores industriais reais calibrados.

| Parâmetro | Limite Inferior | Limite Superior | Unidade | Fonte |
|-----------|----------------|----------------|---------|-------|
| pH | 5.0 | 9.0 | adimensional | Premissa de laboratório didático |
| Turbidez | 0.0 | 100.0 | NTU (simulado) | Premissa de laboratório didático |
| TOC | 0.0 | 50.0 | mg/L (simulado) | Premissa de laboratório didático |

**Drift** é detectado quando a média móvel das últimas 5 leituras se desvia
mais de 1.5 desvios padrão da média histórica do mesmo sensor.

## Relacionamentos

```
TelemetrySensor 1──N TelemetryReading
TelemetrySensor 1──N TelemetryAlert
```

## Notas Técnicas

- Timestamps são armazenados em UTC (`USE_TZ=True`).
- Não há soft delete — linhas são físicas e não removidas após criação.
- O campo `source` (origem da leitura: simulator, modbus) não é persistido
  em `TelemetryReading` — esta é uma limitação conhecida documentada como
  evolução futura.
