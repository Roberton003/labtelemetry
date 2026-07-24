[[Home]] | [[Overview]] | [[Architecture]] | [[Idempotencia-e-Replay]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# ✅ Guia de Validação

Roteiro para validar o pipeline inteiro localmente, do simulador ao gráfico:

```text
ingestão → regras de qualidade → PostgreSQL → API JSON → dashboard HTMX/Chart.js
```

Todos os comandos assumem que você está na raiz do repositório clonado.

---

## 🖥️ Execução em Terminais Paralelos

### Terminal A — Infraestrutura

```bash
docker compose up -d
docker compose ps
```

**Esperado:** `labtelemetry_postgres` e `labtelemetry_jaeger` em execução.

### Terminal B — Banco e Aplicação

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py migrate
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
```

**Esperado:** migrations aplicadas sem erro; servidor escutando na 8000.

### Terminal C — Dados e Checagens HTTP

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once

curl -sS "http://127.0.0.1:8000/api/summary/"
curl -sS "http://127.0.0.1:8000/api/readings/recent/?limit=3"
curl -sS "http://127.0.0.1:8000/api/health/sources/"
```

**Esperado:**

- `total_sensors > 0` e `total_readings > 0`
- leituras recentes trazem `source: "simulator:seed=42"`
- saúde da fonte reporta `simulator: ok`

---

## 🔁 Validar a Idempotência

O ponto mais fácil de errar ao avaliar o projeto. Execute a ingestão de novo:

```bash
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once
curl -sS "http://127.0.0.1:8000/api/summary/"
```

**Esperado:** a contagem **cresce** — e isso está correto. O `SimulatorAdapter` carimba `timestamp = agora`, então cada execução é uma janela nova. A garantia de idempotência vale para o mesmo par `(sensor, timestamp)`, e é verificada pelo teste automatizado:

```bash
.venv/bin/python labtelemetry/manage.py test \
  telemetry.test_ingest_telemetry.IngestTelemetryCommandTest.test_replay_same_window_is_idempotent
```

O raciocínio completo está em [[Idempotencia-e-Replay]].

---

## 🌐 Validação no Navegador

Abra `http://127.0.0.1:8000/` e confirme:

1. o título renderiza como LabTelemetry
2. os cards de resumo mostram sensores e leituras
3. a aba de leituras recentes contém linhas
4. o painel de saúde das fontes mostra o simulador como `ok`
5. o gráfico renderiza — canvas em branco é falha

<p align="center">
  <img src="assets/dashboard_mockup.png" alt="Dashboard LabTelemetry" width="88%">
</p>

---

## 🔭 Tracing Opcional

```bash
export OTEL_ENABLED=True
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000

curl -sS "http://127.0.0.1:8000/api/summary/"
curl -sS "http://127.0.0.1:16686/api/traces?service=labtelemetry&limit=5"
```

**Esperado:** o Jaeger devolve traces do serviço `labtelemetry`. Sem `OTEL_ENABLED=True`, nenhum trace é emitido — por design.

---

## 🎯 Critérios de Sucesso

- o dashboard renderiza com gráfico populado
- a saúde das fontes reporta o simulador como `ok`
- `/api/summary/` devolve sensores e leituras não-zerados
- as leituras recentes expõem o campo `source`
- `manage.py test telemetry` segue verde depois de toda a execução (73 testes)
