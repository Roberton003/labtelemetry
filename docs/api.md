# API Reference

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

## Examples

```bash
curl -s http://127.0.0.1:8000/api/summary/
curl -s http://127.0.0.1:8000/api/health/sources/
```

## Notes

- Legacy bare API routes without `/api/` are not part of the public contract.
- The source health endpoint is operational metadata. It does not replace a live Modbus connectivity test.
