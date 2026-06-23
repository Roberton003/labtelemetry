# SQL Analítico — LabTelemetry

Consultas SQL compatíveis com PostgreSQL para análise exploratória dos dados
de telemetria. Úteis para avaliação de portfólio, debugging e validação de
qualidade.

## Como usar

```bash
# Conectar ao banco PostgreSQL via docker
docker compose exec -T postgres psql -U labtelemetry -d labtelemetry -f sql/analytics/volume_por_janela.sql

# Ou via pipe com DATABASE_URL
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
psql "$DATABASE_URL" -f sql/analytics/taxa_anomalia.sql
```

## Consultas

| Arquivo | O que responde |
|---------|---------------|
| `volume_por_janela.sql` | Leituras por hora/dia e por parâmetro |
| `taxa_anomalia.sql` | Percentual de leituras anômalas por sensor |
| `leituras_recentes.sql` | Últimas 50 leituras com status e alertas |
| `sensores_com_alerta.sql` | Sensores com alerta ativo e recência |
| `freshness.sql` | Idade da última leitura por sensor (freshness) |

## Notas

- As consultas refletem o schema atual do Django (sem campo `source`).
- Para SQLite, adaptar funções de data/hora (`NOW()` → `datetime('now')`).
- Valores de threshold são premissas de laboratório (ver `docs/data-model.md`).
