# LabTelemetry

<p align="center">
  <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="Django 5" src="https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white">
  <img alt="PostgreSQL 16" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white">
  <img alt="OpenTelemetry" src="https://img.shields.io/badge/OpenTelemetry-4B9CD3?logo=opentelemetry&logoColor=white">
  <img alt="Jaeger" src="https://img.shields.io/badge/Jaeger-66CFE3?logo=jaeger&logoColor=white">
  <img alt="HTMX" src="https://img.shields.io/badge/HTMX-3366CC?logo=htmx&logoColor=white">
  <img alt="Chart.js" src="https://img.shields.io/badge/Chart.js-FF6384?logo=chartdotjs&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white">
</p>

<p align="center">
  Reproducible OT/IT telemetry lab with simulation, quality rules, JSON API, dashboard, and local observability.
</p>

LabTelemetry is a Django project built to demonstrate a complete telemetry path without inflating the stack beyond what the use case needs:

`simulator -> ingestion -> quality evaluation -> PostgreSQL/SQLite -> JSON API -> dashboard`

## Platform Snapshot

| Area | Current State |
|---|---|
| Domain | Industrial telemetry lab for pH, turbidity, and TOC |
| Ingestion | Deterministic simulator plus Modbus TCP adapter surface |
| Storage | PostgreSQL 16 via Docker Compose, SQLite fallback for local-only runs |
| Backend | Django 5.2.9 |
| Frontend | Server-rendered dashboard with HTMX and Chart.js |
| Observability | OpenTelemetry with Jaeger, optional at runtime |
| Data Quality | Threshold rules, drift warning, active alerts |
| Validation | Django tests, API checks, end-to-end local manual |

## What You Can Validate Today

- Reproducible local ingestion from a controlled simulator
- Persistent telemetry readings with source lineage
- JSON endpoints under `/api/...`
- Operational dashboard rendered by Django
- Source health checks for simulator and Modbus
- Optional traces in Jaeger

## Architecture

```mermaid
graph TD
    A[Simulated or Modbus source] --> B[Ingestion command]
    B --> C[Quality rules and alerts]
    C --> D[(PostgreSQL or SQLite)]
    D --> E[JSON API]
    E --> F[Dashboard with HTMX and Chart.js]
    E --> G[OpenTelemetry traces]
    G --> H[Jaeger]
```

## Quick Start

### 1. Bootstrap

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
docker compose up -d
```

### 2. Migrate and run

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
```

### 3. Generate telemetry

```bash
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
curl -s http://127.0.0.1:8000/api/summary/
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Jaeger: `http://127.0.0.1:16686`

## Documentation Map

| Document | Purpose |
|---|---|
| `docs/overview.md` | Project scope and public positioning |
| `docs/architecture.md` | Runtime structure and component boundaries |
| `docs/api.md` | API endpoints and public contract notes |
| `docs/operations.md` | Local setup and operational commands |
| `docs/manual_validacao_ponta_a_ponta.md` | Full end-to-end validation in parallel terminals |
| `docs/data-model.md` | Operational data model and semantics |
| `docs/data-contract.md` | Public API and data contract |
| `docs/replay-idempotency.md` | Replay, deduplication, and idempotency behavior |
| `sql/analytics/` | Example analytical SQL queries |
| `docs/security.md` | Public documentation boundary and secret handling |

## Frontend Status

The project already includes a frontend. It is not a separate SPA; the user interface is delivered by Django templates and consumes the JSON API with HTMX and Chart.js.

Current UI scope:

- summary cards
- source health panel
- recent readings tab
- active alerts tab
- sensor list tab
- time-series chart

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
curl -s "http://127.0.0.1:16686/api/traces?service=labtelemetry&limit=5"
```

## Validation

### Fast sanity

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry --verbosity=1
```

### Full practical flow

Use the manual in `docs/manual_validacao_ponta_a_ponta.md`.

That guide validates:

- infrastructure
- migrations
- ingestion
- API
- dashboard partials
- browser flow
- optional tracing

## Current Boundaries

This repository is intentionally scoped as a local lab and portfolio-grade system, not a generalized production platform.

Out of current public scope:

- full production auth
- public cloud deployment
- distributed streaming
- heavy orchestration
- real PLC validation as a default path

## Wiki

The project wiki is available at:

- `https://github.com/Roberton003/labtelemetry/wiki`
