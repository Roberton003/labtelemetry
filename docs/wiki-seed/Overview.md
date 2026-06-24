[[Home]] | [[Overview]] | [[Architecture]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# Overview

LabTelemetry is a Django-based OT/IT telemetry lab. It simulates industrial sensor readings, persists time-series data, applies data quality rules, exposes JSON endpoints, and renders an operational dashboard.

The project is intentionally small and reproducible. It demonstrates the path from operational telemetry to an application-facing data product without introducing distributed data platforms before they are needed.

## Core Capabilities

- Industrial telemetry simulation for pH, turbidity, and TOC
- PostgreSQL support with SQLite fallback for local development
- Data quality rules for normal readings, out-of-bounds values, and drift warnings
- Active operational alerts
- JSON API under `/api/...`
- Django dashboard with HTMX and Chart.js
- Optional OpenTelemetry tracing with Jaeger
- Extensible source adapters for simulator and Modbus TCP ingestion

## Why This Project Exists

Many data projects demonstrate tools but not the shape of operational data at the source. LabTelemetry stays intentionally small so the path from telemetry generation to application-facing consumption is visible, testable, and robust.

## Public Positioning

LabTelemetry is best understood as:

1. a reproducible OT/IT telemetry lab
2. a portfolio project with real operational flow
3. a compact data product
