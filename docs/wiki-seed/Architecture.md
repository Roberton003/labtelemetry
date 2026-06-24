# Architecture

LabTelemetry follows a simple layered architecture:

```text
Telemetry source
  -> ingestion command
  -> quality evaluation
  -> database
  -> JSON API
  -> dashboard
```

## Runtime Components

- `telemetry.models`: sensor, reading, and alert persistence models
- `telemetry.quality`: threshold and drift evaluation rules
- `telemetry.management.commands.simulate_telemetry`: deterministic telemetry simulation
- `telemetry.management.commands.telemetry_simulate`: operational wrapper for repeated simulation
- `telemetry.management.commands.ingest_telemetry`: source-based ingestion command
- `telemetry.sources`: source adapter abstraction for simulator and Modbus TCP
- `telemetry.views`: dashboard and JSON API views

## Data Model

- `TelemetrySensor`: monitored point, parameter, status, and calibration factor
- `TelemetryReading`: timestamped raw and calibrated value, source lineage, and quality status
- `TelemetryAlert`: active or resolved operational alert

## Source Adapters

The ingestion layer separates data sources from persistence. Each persisted reading stores the logical source name used during ingestion so recent-reading queries retain basic lineage without preserving raw protocol payloads.

Current adapters:

- `SimulatorAdapter`: reproducible local runs
- `ModbusTCPAdapter`: configurable host, port, unit id, and timeout

The simulator remains the default reproducible path. Real Modbus validation depends on an available device or simulator.
