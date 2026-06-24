# LabTelemetry

<p align="center">
  <img src="docs/assets/labtelemetry_hero_banner.png" alt="LabTelemetry banner" width="100%">
</p>

<p align="center">
  <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Django 5" src="https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white">
  <img alt="PostgreSQL 16" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
  <img alt="OpenTelemetry" src="https://img.shields.io/badge/OpenTelemetry-4B9CD3?style=for-the-badge&logo=opentelemetry&logoColor=white">
  <img alt="Jaeger" src="https://img.shields.io/badge/Jaeger-66CFE3?style=for-the-badge&logo=jaeger&logoColor=white">
  <img alt="HTMX" src="https://img.shields.io/badge/HTMX-3366CC?style=for-the-badge&logo=htmx&logoColor=white">
  <img alt="Chart.js" src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
</p>

<p align="center">
  Reproducible OT/IT telemetry lab with simulation, quality rules, JSON API, dashboard, and local observability.
</p>

## Overview

LabTelemetry is a Django project built to demonstrate a complete telemetry path without inflating the stack beyond what the use case needs.

```text
simulator -> ingestion -> quality evaluation -> PostgreSQL/SQLite -> JSON API -> dashboard
```

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

## Dashboard

<p align="center">
  <img src="docs/assets/dashboard_mockup.png" alt="LabTelemetry dashboard mockup" width="90%">
</p>

The user interface is built with Django templates, HTMX, and Chart.js.

## Documentation Map

| Document | Purpose |
|---|---|
| [docs/overview.md](docs/overview.md) | Project scope and public positioning |
| [docs/architecture.md](docs/architecture.md) | Runtime structure and component boundaries |
| [docs/api.md](docs/api.md) | API endpoints and public contract notes |
| [docs/operations.md](docs/operations.md) | Local setup and operational commands |
| [docs/manual_validacao_ponta_a_ponta.md](docs/manual_validacao_ponta_a_ponta.md) | Full end-to-end validation in parallel terminals |
| [docs/data-model.md](docs/data-model.md) | Operational data model and database schemas |
| [docs/data-contract.md](docs/data-contract.md) | Public API and data contract definition |
| [docs/replay-idempotency.md](docs/replay-idempotency.md) | Replay, deduplication, and idempotency behavior |
| [docs/security.md](docs/security.md) | Public documentation boundary and secret handling |

## Quick Start

### Bootstrap Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d
```

### Migrate and Run

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
python labtelemetry/manage.py migrate
python labtelemetry/manage.py runserver 127.0.0.1:8000
```

### Generate Telemetry

```bash
python labtelemetry/manage.py ingest_telemetry --source simulator --once
curl -s http://127.0.0.1:8000/api/summary/
```

Open locally:

- Dashboard: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Jaeger: http://127.0.0.1:16686

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

### Fast Sanity

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry --verbosity=1
```

### Full Practical Flow

Use [docs/manual_validacao_ponta_a_ponta.md](docs/manual_validacao_ponta_a_ponta.md) for the parallel-terminal walkthrough.

## Boundaries

This repository is intentionally scoped as a local lab and portfolio-grade system, not a generalized production platform.

Out of current public scope:

- distributed stream processing
- production authentication
- multi-region cloud infrastructure

## Wiki

The project wiki is available at:

- https://github.com/Roberton003/labtelemetry/wiki
