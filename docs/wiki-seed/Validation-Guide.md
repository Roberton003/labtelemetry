[[Home]] | [[Overview]] | [[Architecture]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# Validation Guide

This guide validates the full local flow:

`simulator -> ingestion -> PostgreSQL -> JSON API -> Django/HTMX/Chart.js dashboard`

## Parallel Execution

Use 3 terminals.

### Terminal A - Infrastructure

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
docker compose up -d
```

Expected:

- `labtelemetry_postgres` running
- `labtelemetry_jaeger` running

### Terminal B - Database And App

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
```

### Terminal C - Data And HTTP Checks

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
curl -sS "http://127.0.0.1:8000/api/summary/"
curl -sS "http://127.0.0.1:8000/api/readings/recent/?limit=3"
curl -sS "http://127.0.0.1:8000/api/health/sources/"
```

Expected:

- `total_sensors > 0`
- `total_readings > 0`
- recent readings contain `source: "simulator:seed=42"`
- source health returns `simulator: ok`

## Browser Validation

Open `http://127.0.0.1:8000/` and confirm:

- LabTelemetry title renders
- summary cards show sensors and readings
- recent readings tab contains rows
- source health shows simulator as `ok`
- chart renders without a blank canvas

## Optional Tracing

```bash
export OTEL_ENABLED=True
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
curl -sS "http://127.0.0.1:16686/api/traces?service=labtelemetry&limit=5"
```

## What Success Looks Like

- the dashboard renders
- source health shows simulator as `ok`
- API summary returns non-zero sensors and readings
- recent readings expose `source`
- test suite remains green after the run
