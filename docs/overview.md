# LabTelemetry Overview

LabTelemetry is a Django-based OT/IT telemetry lab. It simulates industrial sensor readings, persists time-series data, applies data quality rules, exposes JSON endpoints, and renders an operational dashboard.

The project is intentionally small and reproducible. It demonstrates the path from operational telemetry to an application-facing data product without introducing distributed data platforms before they are needed.

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

## What It Shows

- reproducible local ingestion from a controlled simulator
- persistent telemetry readings with source lineage
- JSON endpoints under `/api/...`
- a server-rendered dashboard with dynamic HTMX updates
- source health checks for simulator and Modbus
- optional traces in Jaeger

## Why It Exists

Many data projects demonstrate tools but not the shape of operational data at the source. LabTelemetry stays intentionally small so the path from telemetry generation to application-facing consumption is visible, testable, and robust.

## Public Positioning

LabTelemetry is best understood as:

1. a reproducible OT/IT telemetry lab
2. a portfolio project with real operational flow
3. a compact data product
