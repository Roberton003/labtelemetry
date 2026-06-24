# Manual De Validacao Ponta A Ponta

Este manual valida o fluxo completo do LabTelemetry em execucao local:

`simulator -> ingestao -> PostgreSQL -> API JSON -> dashboard Django/HTMX/Chart.js`

O projeto ja possui frontend. Ele nao e uma SPA separada; a interface e
servida pelo proprio Django em templates HTML com HTMX e Chart.js.

## Pre-Requisitos

- Docker e Docker Compose instalados
- ambiente virtual `.venv` criado
- dependencias instaladas com `pip install -r requirements.txt`
- porta `8000` livre para o Django
- portas `5432`, `16686` e `4318` livres para PostgreSQL/Jaeger/OTLP

## Execucao Em Paralelo

Use 3 terminais.

### Terminal A - Infraestrutura

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
docker compose up -d
```

Resultado esperado:

- container `labtelemetry_postgres` em `Running`
- container `labtelemetry_jaeger` em `Running`

### Terminal B - Banco E Aplicacao

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
```

Resultado esperado:

- `System check identified no issues`
- servidor iniciado em `http://127.0.0.1:8000/`

### Terminal C - Dados E Verificacao

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
curl -sS "http://127.0.0.1:8000/api/summary/"
curl -sS "http://127.0.0.1:8000/api/readings/recent/?limit=3"
curl -sS "http://127.0.0.1:8000/api/health/sources/"
```

Resultado esperado:

- ingestao com `6 samples, 6 readings`
- `/api/summary/` com `total_sensors > 0` e `total_readings > 0`
- `/api/readings/recent/` retornando leituras com `source: "simulator:seed=42"`
- `/api/health/sources/` retornando `simulator: ok`

## Validacao Manual No Navegador

Com os 3 terminais em execucao:

1. Abrir `http://127.0.0.1:8000/`
2. Confirmar que o titulo `LabTelemetry` aparece
3. Confirmar que os cards de resumo mostram sensores e leituras
4. Confirmar que a aba `Leituras Recentes` mostra linhas na tabela
5. Confirmar que a secao `Fontes de Dados` mostra:
   `Simulator:Seed=42 -> ok`
6. Confirmar que o grafico de leituras renderiza sem tela vazia

## Validacao HTTP Dos Partials Do Dashboard

```bash
curl -sS "http://127.0.0.1:8000/dashboard/cards/" | head -40
curl -sS "http://127.0.0.1:8000/dashboard/readings/" | head -40
curl -sS "http://127.0.0.1:8000/dashboard/health/" | head -40
```

Resultado esperado:

- `/dashboard/cards/` retorna HTML com `Sensores`, `Leituras`, `Alertas`
- `/dashboard/readings/` retorna tabela HTML com leituras recentes
- `/dashboard/health/` retorna cards HTML de `simulator` e `modbus`

## Validacao Opcional De Tracing

Em um quarto terminal ou reaproveitando o Terminal B:

```bash
cd "/media/Arquivos/Engenharia dados IOT 2026/labtelemetry"
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
export OTEL_ENABLED=True
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
```

E em outro terminal:

```bash
curl -sS "http://127.0.0.1:8000/api/summary/"
curl -sS "http://127.0.0.1:16686/api/traces?service=labtelemetry&limit=5"
```

Resultado esperado:

- Jaeger respondendo em `http://127.0.0.1:16686`
- consulta de traces retornando JSON

## Sequencia Minima De Sanidade

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry --verbosity=1
```

Resultado esperado:

- `check`: sem issues
- `makemigrations --check --dry-run`: `No changes detected`
- `test telemetry --verbosity=1`: suite verde

## Problemas Reais Encontrados E Como Resolver

### Migration nao aplicada no PostgreSQL

Sintoma:

- o servidor sobe, mas avisa sobre migration pendente da app `telemetry`

Correcao:

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
```

### Leituras recentes em ordem inconsistente

Sintoma:

- leituras com mesmo `timestamp` aparecem em ordem ambigua

Estado atual:

- resolvido no codigo com ordenacao por `-timestamp, -id`

## Encerramento

Para parar tudo:

### Terminal B

- `Ctrl+C`

### Terminal A

```bash
docker compose down
```

Se quiser manter PostgreSQL e Jaeger para outra rodada, nao derrube os
containers.
