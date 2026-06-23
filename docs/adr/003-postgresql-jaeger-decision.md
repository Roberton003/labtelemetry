# ADR 003: PostgreSQL + Jaeger para Infraestrutura de Telemetria

- **Data:** 2026-06-22
- **Autor:** Roberto (via OpenCode Lead Agent)
- **Status:** Aceito

## Contexto

O LabTelemetry foi prototipado com SQLite (desenvolvimento) e sem observabilidade
distribuída. Para sustentar o MVP com dados reais de telemetria F1/industrial IoT,
é necessária uma base de dados concorrente e um pipeline de tracing distribuído.

Requisitos:
- Múltiplos sensores escrevendo simultaneamente (concorrência)
- Consultas analíticas com agregação temporal
- Rastreamento de requisições HTTP e queries de banco (tracing)
- Perfilamento de latência por camada (HTTP → Django → banco)

## Decisão

### PostgreSQL como banco de dados principal

- **Engine:** PostgreSQL 16 Alpine (container Docker)
- **Driver:** psycopg[binary] v3 (`opentelemetry-instrumentation-psycopg`)
- **Pool:** `conn_max_age=600` via `dj_database_url`
- **Schema:** Mesmo modelo Django existente (migrações 0001 + 0002)
- **Porta:** 5432 (host) / 5432 (container)
- **Dados locais:** Volume Docker `pgdata` persistido

### Jaeger como backend de tracing (OTLP)

- **Engine:** Jaeger all-in-one (container Docker)
- **Protocolo:** OTLP HTTP (porta 4318)
- **UI:** Porta 16686
- **Instrumentação:** OpenTelemetry SDK Python + DjangoInstrumentor + PsycopgInstrumentor
- **Ativação condicional:** `OTEL_ENABLED=True` via variável de ambiente
- **Service name:** `labtelemetry`

### Semântica de tracing

- Service name: `labtelemetry`
- Exporter: OTLP HTTP (`http://localhost:4318/v1/traces`)
- Processor: BatchSpanProcessor (default)
- Spans capturados: requisições Django, queries psycopg, spans manuais se necessário

## Consequências

### Positivas

- Concorrência real: PostgreSQL suporta múltiplas conexões simultâneas
- Tracing distribuído permite debug de latência por camada
- Jaeger UI dá visibilidade em tempo real das requisições
- OTLP é padrão aberto — possível migrar para Grafana Tempo ou SigNoz sem
  mudar instrumentação
- Ambas rodam em Docker — `docker compose up` provisiona toda a stack

### Negativas

- PostgreSQL exige mais memória que SQLite (~100MB vs ~5MB)
- Dependência de Docker para ambiente local
- Backup/restore mais complexo que SQLite (dump SQL vs copiar arquivo)
- Tracing adiciona overhead de CPU (~1-3% em dev, desprezível)

### Mitigações

- SQLite continua disponível como fallback (default da DATABASE_URL)
- Tracing é condicional (`OTEL_ENABLED=False` por padrão)
- migrate/rollback usa Django migrations padrão

## Alternativas Rejeitadas

### SQLite em produção

- **Motivo da rejeição:** Sem concorrência (write lock serializa), sem suporte
  a conexões simultâneas, sem type casting para timestamp em consultas agregadas.
- **Quando usar:** Apenas desenvolvimento local / testes unitários (default).

### DuckDB como serving layer

- **Motivo da rejeição:** Excelente para analytics, mas sem suporte a
  upsert/concorrência transacional. Seria camada adicional de complexidade.
- **Quando usar:** Futuro, se houver necessidade de queries analíticas pesadas
  separadas do OLTP.

### Prometheus + Grafana (métricas)

- **Motivo da rejeição:** Foco atual é tracing distribuído, não métricas.
  Prometheus seria camada extra de coleta sem benefício imediato.
- **Quando usar:** Futuro, se houver necessidade de alerting/SLO.

### Sentry para tracing

- **Motivo da rejeição:** SaaS, dependência externa, custo por evento.
  Jaeger é self-hosted e gratuito.

## Rollback

Para reverter para SQLite exclusivo:
1. Parar containers: `docker compose down`
2. Remover DATABASE_URL do .env (ou setar `DATABASE_URL=sqlite:///db.sqlite3`)
3. Rodar `python manage.py migrate`
4. Tracing continua desligado (OTEL_ENABLED ausente = False)

## Referências

- Plano 001: `docs/plans/001_implementacao_labtelemetry_pipeline_dashboard_observabilidade.md`
- Management Review: `docs/plans/002_avaliacao_gerencial_entrega_plano_001.md`
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- Jaeger OTLP: https://www.jaegertracing.io/docs/latest/otlp/
