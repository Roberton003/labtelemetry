# API

All JSON endpoints are served under `/api/`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/sensors/` | List sensors |
| GET | `/api/readings/recent/?limit=50` | Return recent readings |
| GET | `/api/sensors/<id>/readings/?limit=100` | Return readings for one sensor |
| GET | `/api/alerts/active/` | Return active alerts |
| GET | `/api/summary/` | Return operational summary |
| GET | `/api/health/sources/` | Return telemetry source status |

## Notes

- Reading payloads include `source`, a short lineage field such as `simulator:seed=42` or `modbus:host:port`
- Legacy bare API routes without `/api/` are not part of the public contract
- The source health endpoint is operational metadata; it does not replace a live Modbus connectivity test

## Example

```bash
curl -s http://127.0.0.1:8000/api/summary/
curl -s http://127.0.0.1:8000/api/health/sources/
```
