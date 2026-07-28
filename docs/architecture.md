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

- `telemetry.models`: sensor, reading, and alert persistence models.
- `telemetry.quality`: threshold and drift evaluation rules.
- `telemetry.management.commands.simulate_telemetry`: deterministic telemetry simulation.
- `telemetry.management.commands.ingest_telemetry`: source-based ingestion command.
- `telemetry.sources`: source adapter abstraction for simulator, Modbus TCP, and OPC-UA.
- `telemetry.views`: dashboard and JSON API views.

## Data Model

- `TelemetrySensor`: monitored point, parameter, status, and calibration factor.
- `TelemetryReading`: timestamped raw and calibrated value, source lineage, and quality status.
- `TelemetryAlert`: active or resolved operational alert.

## Source Adapters

The ingestion layer separates data sources from persistence. Each persisted
reading stores the logical source name used during ingestion so recent-reading
queries retain basic lineage without preserving raw protocol payloads.

The current adapters are:

- `SimulatorAdapter`: uses the existing simulator path for reproducible local runs.
- `ModbusTCPAdapter`: configurable host, port, unit id, and timeout. Each
  holding register is mapped to the sensor it feeds, with its own scale
  factor — a uint16 register cannot hold a pH of 7.40, so the PLC publishes
  740 and the mapping converts it back.
- `OpcUaAdapter`: reads node variables from an OPC-UA server. Each node is
  mapped to the sensor it feeds; positional node index is not a sensor
  primary key, so the mapping is required rather than inferred.

The simulator remains the default reproducible path. Real Modbus and OPC-UA validation depend on an available device or simulator.
