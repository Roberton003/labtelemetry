# LabTelemetry

LabTelemetry e um laboratorio Django para simular telemetria industrial OT/IT, persistir leituras temporais, aplicar quality gates, expor API JSON e visualizar o estado operacional em dashboard web.

Documentacao publica:

- Visao geral: `docs/overview.md`
- Arquitetura: `docs/architecture.md`
- API: `docs/api.md`
- Operacao local: `docs/operations.md`
- Politica de documentacao publica: `docs/security.md`

## Stack

- Python 3.12
- Django 5.2.9
- PostgreSQL 16 via Docker Compose
- SQLite como fallback local
- OpenTelemetry Python com DjangoInstrumentor e PsycopgInstrumentor
- Jaeger all-in-one para tracing
- HTMX para atualizacao parcial do dashboard
- Chart.js para grafico temporal

## Arquitetura

```mermaid
graph TD
    A[Sensores simulados] --> B[Django management command]
    B --> C[Quality gates]
    C --> D[(PostgreSQL ou SQLite)]
    C --> E[Alertas ativos]
    D --> F[API JSON /api]
    E --> F
    F --> G[Dashboard HTMX + Chart.js]
    F --> H[OpenTelemetry traces]
    H --> I[Jaeger]
```

## Setup Local

Crie e ative um ambiente virtual Python antes de instalar dependencias.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Suba a infraestrutura local:

```bash
docker compose up -d
```

Servicos esperados:

- PostgreSQL: `localhost:5432`
- Jaeger UI: `http://127.0.0.1:16686`
- OTLP HTTP: `http://localhost:4318`

## Banco De Dados

SQLite e o fallback quando `DATABASE_URL` nao esta definido.

Para usar PostgreSQL:

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
```

## Simulacao De Telemetria

Comando principal, alinhado ao Plano 001:

```bash
.venv/bin/python labtelemetry/manage.py simulate_telemetry --once --seed 42 --sensors 6
```

Alias operacional para gerar multiplas iteracoes:

```bash
.venv/bin/python labtelemetry/manage.py telemetry_simulate --seed 42 --count 50
```

O simulador cria leituras para sensores padrao quando necessario e aplica os quality gates antes de persistir o status final.

## Fontes De Dados

O LabTelemetry trabalha com duas origens principais na camada de ingestao:

- `simulator`: fonte controlada para laboratorio, testes e reproducoes deterministicas;
- `modbus`: adapter TCP para fonte OT real, com host, porta, unit id e timeout configuraveis.

Comando de ingestao unificado:

```bash
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source modbus --modbus-host 127.0.0.1 --modbus-port 502 --modbus-unit 1
```

Health operacional das fontes:

```bash
curl -s http://127.0.0.1:8000/api/health/sources/
```

O endpoint retorna um resumo por fonte com status e metadados basicos. O simulador e o adapter Modbus permanecem acessiveis como classes separadas em `telemetry.sources`.

## Executar A Aplicacao

Sem tracing:

```bash
.venv/bin/python labtelemetry/manage.py runserver
```

Com tracing OpenTelemetry:

```bash
OTEL_ENABLED=True .venv/bin/python labtelemetry/manage.py runserver
```

Acesse:

- Dashboard: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`
- Jaeger: `http://127.0.0.1:16686`

## API REST JSON

Endpoints atuais:

- `GET /api/sensors/`
- `GET /api/readings/recent/?limit=50`
- `GET /api/sensors/<id>/readings/?limit=100`
- `GET /api/alerts/active/`
- `GET /api/summary/`
- `GET /api/health/sources/`

Exemplo:

```bash
curl -s http://127.0.0.1:8000/api/summary/
```

As rotas antigas sem prefixo `/api/` devem retornar `404`.

## Dashboard

O dashboard combina:

- cards e tabelas atualizados por HTMX;
- grafico temporal com Chart.js;
- consumo da API `/api/readings/recent/`;
- polling simples para atualizar leituras e indicadores.

## OpenTelemetry E Jaeger

Tracing fica desligado por padrao:

```bash
OTEL_ENABLED=False
```

Para validar traces:

```bash
docker compose up -d
OTEL_ENABLED=True .venv/bin/python labtelemetry/manage.py runserver
curl -s http://127.0.0.1:8000/api/summary/
curl -s "http://localhost:16686/api/traces?service=labtelemetry&limit=5"
```

Instrumentacao configurada:

- DjangoInstrumentor para requests Django;
- PsycopgInstrumentor para psycopg v3;
- exporter OTLP HTTP para `http://localhost:4318/v1/traces`.

## Quality Gates

Parametros iniciais:

- `PH`: minimo `6.0`, maximo `8.5`
- `TURBIDITY`: maximo `5.0`
- `TOC`: maximo `10.0`

Classificacoes:

- `NORMAL`
- `OUT_OF_BOUNDS`
- `DRIFT_WARNING`

Leituras anomalas podem gerar `TelemetryAlert` ativo, com deduplicacao por sensor e tipo de status.

## Validacao

Comandos locais:

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry
.venv/bin/python labtelemetry/manage.py simulate_telemetry --once --seed 42 --sensors 6
.venv/bin/python labtelemetry/manage.py telemetry_simulate --seed 42 --count 50
```

Testes contra PostgreSQL:

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py test telemetry
```
