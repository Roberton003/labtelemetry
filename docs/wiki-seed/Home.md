# LabTelemetry Wiki

LabTelemetry is a Django OT/IT telemetry lab focused on a reproducible end-to-end flow:

`simulator -> ingestion -> quality evaluation -> PostgreSQL/SQLite -> JSON API -> dashboard`

## Start Here

- [[Overview]]
- [[Architecture]]
- [[API]]
- [[Operations]]
- [[Validation-Guide]]

## What This Project Already Has

- Industrial telemetry simulation for pH, turbidity, and TOC
- PostgreSQL support with SQLite fallback
- Quality gates and operational alerts
- JSON API under `/api/...`
- Server-rendered dashboard with HTMX and Chart.js
- Optional OpenTelemetry tracing with Jaeger
- Source adapters for simulator and Modbus TCP

## Current Scope

This wiki covers how to understand, run, and validate the public project.
Private planning material, internal notes, and session records stay out of the wiki.
