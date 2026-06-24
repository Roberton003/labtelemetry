# Operations

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
docker compose up -d
.venv/bin/python labtelemetry/manage.py migrate
```

## Run The Application

```bash
.venv/bin/python labtelemetry/manage.py runserver
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Jaeger: `http://127.0.0.1:16686`

## Generate Telemetry

```bash
.venv/bin/python labtelemetry/manage.py simulate_telemetry --once --seed 42 --sensors 6
.venv/bin/python labtelemetry/manage.py telemetry_simulate --seed 42 --count 50
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
```

## Validation

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry --verbosity=1
```

For a full parallel terminal validation flow, see [[Validation-Guide]].
