# Operations

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
docker compose up -d
```

## Database

SQLite is the fallback when `DATABASE_URL` is not set.

For PostgreSQL:

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
```

## Run The Application

```bash
.venv/bin/python labtelemetry/manage.py runserver
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Jaeger: `http://127.0.0.1:16686`

## Generate Telemetry

```bash
.venv/bin/python labtelemetry/manage.py simulate_telemetry --once --seed 42 --sensors 6
.venv/bin/python labtelemetry/manage.py telemetry_simulate --seed 42 --count 50
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
```

## What The UI Shows

- summary cards
- source health
- recent readings
- active alerts
- sensor list
- a time-series chart rendered with Chart.js

## Observability

Tracing is disabled by default:

```bash
OTEL_ENABLED=False
```

To validate traces locally:

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
OTEL_ENABLED=True .venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
curl -s http://127.0.0.1:8000/api/summary/
curl -s "http://localhost:16686/api/traces?service=labtelemetry&limit=5"
```

## Validation

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry --verbosity=1
```

For a full parallel-terminal walkthrough, use [docs/manual_validacao_ponta_a_ponta.md](docs/manual_validacao_ponta_a_ponta.md).
