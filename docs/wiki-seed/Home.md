[[Home]] | [[Overview]] | [[Architecture]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# LabTelemetry Wiki

<p align="center">
  <img src="assets/labtelemetry_hero_banner.png" alt="LabTelemetry banner" width="100%">
</p>

LabTelemetry is a Django OT/IT telemetry lab designed to be read, run, and validated quickly.

`simulator -> ingestion -> quality evaluation -> PostgreSQL/SQLite -> JSON API -> dashboard`

## Navigation

| Start Here | Reference |
|---|---|
| [[Overview]] | [[API]] |
| [[Architecture]] | [[Operations]] |
| [[Validation-Guide]] | |

## Platform Snapshot

| Area | Current State |
|---|---|
| Runtime | Django 5.2.9 |
| Persistence | PostgreSQL 16 via Docker Compose, SQLite fallback |
| UI | Server-rendered dashboard with HTMX and Chart.js |
| Telemetry Sources | Simulator and Modbus TCP adapter surface |
| Observability | Optional OpenTelemetry with Jaeger |
| Validation | Automated tests plus end-to-end local manual |

<p align="center">
  <img src="assets/dashboard_mockup.png" alt="LabTelemetry dashboard mockup" width="92%">
</p>

## Recommended Paths

- understand the project quickly: open [[Overview]]
- inspect runtime boundaries: open [[Architecture]]
- run the system locally: open [[Operations]]
- validate the entire flow in practice: open [[Validation-Guide]]
- inspect the public contract: open [[API]]

## Scope

This wiki covers the public project only. Internal planning, session history, and private notes remain outside the wiki.
