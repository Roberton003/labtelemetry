# Progresso do Plano 001 — LabTelemetry Fases 1-8

## Status Consolidado (2026-06-22)

| Fase | Descrição | Status | Observações |
|------|-----------|--------|-------------|
| 1 | Reprodutibilidade e Configuração | ✅ Completo | requirements.txt, .env.example, settings externalizado, .gitignore |
| 2 | PostgreSQL Local e Migrações | ✅ Código pronto | `docker compose up -d postgres` **não executado** |
| 3 | Quality Gates e Testes de Domínio | ✅ Completo | 45 testes (modelos + quality + command + API + dashboard) |
| 4 | Simulador de Telemetria | ✅ Completo | `simulate_telemetry` --once / --seed / --anomaly-rate |
| 5 | Endpoints REST JSON | ✅ Completo | 8 endpoints Django nativos |
| 6 | Dashboard | ✅ Código pronto | Bootstrap+HTMX (substituiu Chart.js+Alpine.js por simplicidade) |
| 7 | OpenTelemetry no Django | ✅ Código pronto | Instrumentação condicional em settings.py. `docker compose up -d jaeger` **não executado** |
| 8 | Documentação e Fechamento | ⬜ Pendente | README desatualizado, fluxo completo não documentado |

## Checklist Detalhado

### Fase 1: ✅ Completo
- [x] requirements.txt com dependências (Django, psycopg, dj-database-url, python-dotenv, OTel)
- [x] .env.example sem segredos
- [x] settings.py lê SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL, OTEL_* de env vars
- [x] .env ignorado pelo Git (.gitignore contém `.env`)

### Fase 2: ✅ Código Completo (validação Postgres pendente)
- [x] docker-compose.yml com PostgreSQL 16 + Jaeger (unificado)
- [x] DATABASE_URL configurável no .env.example
- [x] Migrações executadas (SQLite em testes)
- [x] Índice composto `(sensor, timestamp)` na migration 0002
- [ ] **⬜ Pendente:** `docker compose up -d postgres` + migrate contra PostgreSQL

### Fase 3: ✅ Completo
- [x] quality.py com Thresholds (PH 6.0-8.5, TURBIDITY <5, TOC <10)
- [x] Classificação: NORMAL, OUT_OF_BOUNDS, DRIFT_WARNING
- [x] evaluate_and_alert com dedup de alertas ativos
- [x] Testes unitários: 17 tests (modelos + quality gates + thresholds)

### Fase 4: ✅ Completo
- [x] simulate_telemetry com --sensors, --anomaly-rate, --seed, --once
- [x] Gera readings, chama quality gates, cria alertas
- [x] 4 testes do comando (reprodutibilidade, anomalias, validações)

### Fase 5: ✅ Completo
- [x] GET /sensors/
- [x] GET /readings/recent/?limit=...
- [x] GET /sensors/<id>/readings/?limit=...
- [x] GET /alerts/active/
- [x] GET /summary/
- [x] 11 testes de API (status code, payload, limites, ordenação)

### Fase 6: ✅ Código Completo
- [x] Dashboard com Bootstrap 5.3 + HTMX 2.0
- [x] Partial views: _cards, _readings, _alerts, _sensors
- [x] Polling 5s/10s via HTMX hx-trigger
- [x] **Decisão:** HTMX substituiu Chart.js+Alpine.js (menos JS, server-rendered)
- [x] 5 testes de renderização dashboard
- [ ] **⬜ Pendente:** Validar manualmente em navegador

### Fase 7: ✅ Código Completo (validação Jaeger pendente)
- [x] Dependências OTel em requirements.txt
- [x] Variáveis OTEL_* em .env.example (OTEL_ENABLED=False por padrão)
- [x] Instrumentação condicional em settings.py (try/except, gated por OTEL_ENABLED)
- [x] Span customizado no endpoint /summary/
- [ ] **⬜ Pendente:** `docker compose up -d jaeger` + testar trace

### Fase 8: ⬜ Pendente
- [ ] **⬜ Pendente:** Atualizar README.md com setup real (PostgreSQL + Jaeger + OTel + simulate)
- [ ] **⬜ Pendente:** Documentar fluxo completo de rollout
- [ ] **⬜ Pendente:** Documentar comandos de verificação validados

## Pendências Globais

| # | Item | Impacto | Quem |
|---|------|---------|------|
| P1 | `.env` não existe (precisa `cp .env.example .env`) | Dev não consegue rodar sem configurar vars | Roberto |
| P2 | PostgreSQL não validado (`docker compose up -d postgres` pendente) | Schema não verificado em PG real | Roberto |
| P3 | Jaeger não validado (`docker compose up -d jaeger` pendente) | Traces OTel não verificados | Roberto |
| P4 | README desatualizado (instruções antigas, sem OTel/PG) | Onboarding quebrado | OpenCode |
| P5 | Fuso horário: simulador usa UTC, settings usa America/Sao_Paulo | Timestamps podem divergir | OpenCode |
| P6 | `opentelemetry-instrumentation-psycopg2` vs `psycopg[binary]` (v3) | Incompatibilidade — instrumento de psycopg2 não instrumenta psycopg v3 | OpenCode |

## Decisões Tomadas vs Plano Original

| Decisão no Plano | O que foi feito | Justificativa |
|-----------------|-----------------|---------------|
| Chart.js + Alpine.js | Bootstrap 5.3 + HTMX 2.0 | Server-rendered simplifica, menos JS para manter |
| DRF no futuro | Views JSON nativas mantidas | Mesma decisão do plano (D005) |
| docker-compose-observability.yml separado | docker-compose.yml unificado (Postgres + Jaeger) | Menos compose files, mais simples |
| `opentelemetry-instrumentation-psycopg` (v3) | `opentelemetry-instrumentation-psycopg2` no requirements | Erro: psycopg v3 não é instrumentado por psycopg2 |

## Testes

```
Ran 47 tests in 0.332s
OK
```

- 45 testes herdados (Fases 1-6)
- 2 novos testes E2E (Fase 8)
- 100% passando em SQLite (memory)

## Arquivos Modificados (Sessão Atual)

- `labtelemetry/labtelemetry/settings.py` — Bloco OTel condicional
- `labtelemetry/telemetry/views.py` — Removeu `import json` não usado, adicionou tracer + span
- `labtelemetry/telemetry/tests.py` — Adicionou EndToEndTest (2 testes)
- `.env.example` — Adicionou `OTEL_ENABLED=False`

## Atualizacao De Saneamento Final (Codex, 2026-06-23)

Esta secao registra o fechamento posterior do saneamento NC-001 a NC-009, sem reescrever o historico original produzido pelo opencode.

### Status Consolidado Apos Saneamento

| Item | Status | Evidencia |
|---|---|---|
| NC-001 API `/api/...` | Concluido | Rotas REST expostas sob `/api/` e rotas antigas cobertas com 404 |
| NC-002 Dashboard HTMX | Concluido | `hx-get` aponta para rotas existentes |
| NC-003 PostgreSQL | Concluido | `docker compose ps`, `migrate` e 53 testes com `DATABASE_URL` PostgreSQL |
| NC-004 Jaeger/OTel | Concluido | Jaeger ativo e OpenTelemetry habilitavel por `OTEL_ENABLED=True` |
| NC-005 psycopg v3 | Concluido | `opentelemetry-instrumentation-psycopg` e `PsycopgInstrumentor` |
| NC-006 Chart.js | Concluido | Dashboard inclui Chart.js e API entrega `parameter`/`value` para o grafico |
| NC-007 README | Concluido | README atualizado com setup e comandos reais |
| NC-008 Testes API/404 | Concluido | 53 testes passam em SQLite e PostgreSQL |
| NC-009 review-loop | Concluido | Revisor adversarial e verificador tecnico executados antes do commit |

### Validacoes Finais

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry
.venv/bin/python labtelemetry/manage.py telemetry_simulate --seed 42 --count 2
DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry" .venv/bin/python labtelemetry/manage.py migrate
DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry" .venv/bin/python labtelemetry/manage.py test telemetry
OTEL_ENABLED=True .venv/bin/python labtelemetry/manage.py check
OTEL_ENABLED=True DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry" .venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
curl -s -o /tmp/labtelemetry_summary.json -w "%{http_code} %{content_type}\n" http://127.0.0.1:8000/api/summary/
curl -s -o /tmp/labtelemetry_traces.json -w "%{http_code} %{content_type}\n" "http://localhost:16686/api/traces?service=labtelemetry&limit=5"
```

Resultado: todos os comandos acima passaram nesta sessao.

Smoke final:

- `/api/summary/`: `200 application/json`;
- Jaeger API: `200 application/json` com `trace_count=5`.

### Observacoes

- `simulate_telemetry` permanece o comando canonico do Plano 001.
- `telemetry_simulate` existe como alias operacional para `--count`.
- O README documenta a stack real: Django, PostgreSQL, Jaeger, OpenTelemetry, HTMX e Chart.js.
- O documento gerencial `docs/plans/002_avaliacao_gerencial_entrega_plano_001.md` preserva a avaliacao do estado anterior ao saneamento e nao deve ser reescrito para mascarar a sequencia historica.
