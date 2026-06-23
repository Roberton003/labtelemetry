# Session Handoff: LabTelemetry Fases 1-6

**Author:** OpenCode (opencode)
**Date:** 2026-06-22
**Project:** labtelemetry
**Platform:** opencode
**Current Objective:** Implementar Fases 1-6 do plano 001 (config → quality gates → simulador → API → dashboard)

> **Nota para sessões futuras (Codex ou outro agente):** Todo handoff deve ser salvo neste mesmo diretório (`docs/session-handoffs/`) com o mesmo formato e nome `YYYYMMDDTHHMMSSfff_slug.md`. O `.last-handoff.json` deve ser atualizado. A autoria (Codex, OpenCode, etc.) deve constar no campo `Author:` do header.

## Decisions

| Decisão | Alternativa Rejeitada | Evidência |
|---------|----------------------|-----------|
| `requirements.txt` em vez de `pyproject.toml` | pyproject.toml | Plano 001 seção 2.1 |
| Thresholds: pH 6.0-8.5, Turb <5, TOC <10 | — | Plano 001 seção 5 |
| Dashboard público sem auth | — | Plano 001 seção 5 |
| `docker-compose.yml` unificado (PostgreSQL + Jaeger) | Separar serviços | Briefing |
| Polling 5s no dashboard | 10s, 30s | Briefing |
| `evaluate_and_alert` salva reading + cria alerta dedup | Apenas avaliar sem persistir | Design |

## Relevant Files

### Criados/Modificados
- `requirements.txt` — dependências (Django 5.2.9, psycopg, dj-database-url, python-dotenv, OTel)
- `.env.example` — variáveis de ambiente
- `.gitignore` — adicionado `.env`
- `labtelemetry/labtelemetry/settings.py` — SECRET_KEY/DEBUG/ALLOWED_HOSTS/DATABASE_URL externalizados via env vars
- `docker-compose.yml` — PostgreSQL 16 + Jaeger
- `labtelemetry/labtelemetry/urls.py` — adicionado `include('telemetry.urls')` na raiz
- `labtelemetry/telemetry/urls.py` — rotas REST + dashboard partials
- `labtelemetry/telemetry/models.py` — índice composto `(sensor, timestamp)`
- `labtelemetry/telemetry/quality.py` — THRESHOLDS, evaluate_reading(), evaluate_and_alert()
- `labtelemetry/telemetry/views.py` — JSON endpoints + dashboard views com HTMX partials
- `labtelemetry/telemetry/management/commands/simulate_telemetry.py` — simulador com --sensors, --anomaly-rate, --seed, --once
- `labtelemetry/telemetry/tests.py` — 45 testes (modelo, quality gates, comando, API, dashboard)
- `labtelemetry/telemetry/migrations/0002_telemetryreading_telemetry_t_sensor__0d3d32_idx.py`
- `labtelemetry/telemetry/templates/telemetry/dashboard.html` + `_cards.html`, `_readings.html`, `_alerts.html`, `_sensors.html`

## Commands/Checks Executed

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py migrate
.venv/bin/python labtelemetry/manage.py test telemetry
# 45 tests, all OK
.venv/bin/python labtelemetry/manage.py runserver 0.0.0.0:8000  # smoke test OK
```

## Open Risks

- PostgreSQL não está rodando localmente (testes usam SQLite em memória). `docker compose up -d` necessário para validar conexão real.
- Fase 7 (OpenTelemetry tracing) e Fase 8 (testes fim-a-fim) não iniciadas.
- Simulador usa `datetime.now(timezone.utc)` mas o `TIME_ZONE` do Django é `America/Sao_Paulo` — consistência de fuso precisa verificação.

## Next Steps

1. **Fase 7:** Integrar OpenTelemetry tracing (config OTel, middleware Django, instrumentação)
2. **Fase 8:** Teste end-to-end (simular → API → verificar dados no dashboard)
3. Validar conexão PostgreSQL com `docker compose up -d`
4. Executar simulador contra ambiente real para validar fluxo completo

## Resume Prompt

```
Retomar a partir de `docs/session-handoffs/20260622T...md`.
Fases 1-6 implementadas, 45 testes passando.
Próximo: Fase 7 (OpenTelemetry tracing) e Fase 8 (teste end-to-end).
Arquivos principais: telemetry/quality.py, telemetry/management/commands/simulate_telemetry.py,
telemetry/views.py, telemetry/templates/telemetry/dashboard.html.
Próximo comando: .venv/bin/python labtelemetry/manage.py test telemetry -v2
```
