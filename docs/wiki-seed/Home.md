[[Home]] | [[Overview]] | [[Architecture]] | [[Idempotencia-e-Replay]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# 🧪 LabTelemetry Wiki

<p align="center">
  <img src="assets/labtelemetry_hero_banner.png" alt="LabTelemetry" width="100%">
</p>

Laboratório de telemetria OT/IT em Django, feito para ser lido, executado e validado rápido. Esta wiki aprofunda o que não cabe no README sem poluí-lo — decisões de design, limites reais do sistema e roteiros de validação.

```text
fonte OT → ingestão → regras de qualidade → PostgreSQL → API JSON → dashboard
```

---

## 📐 Sumário de Documentação

1. **[[Overview]]** — o que é o projeto e por que existe
   - Capacidades principais e posicionamento público
   - O problema que ele torna visível: a forma do dado na origem
   - O que está deliberadamente fora de escopo

2. **[[Architecture]]** — estrutura de runtime e fronteiras
   - Componentes e o que cada um pode ou não conhecer
   - A ABC `TelemetrySource` e os três adapters
   - Modelo de dados e intenção de design

3. **[[Idempotencia-e-Replay]]** — a garantia central, e seus limites
   - Por que a deduplicação vive no banco e não na aplicação
   - O teste negativo que sustenta a garantia
   - O que **não** é garantido, explicitamente

4. **[[API]]** — contrato público JSON
   - Endpoints, formato de payload e campo de lineage
   - O que não faz parte do contrato

5. **[[Operations]]** — setup e comandos do dia a dia
   - Docker e execução local
   - Geração de telemetria por fonte
   - Checagens rápidas de sanidade

6. **[[Validation-Guide]]** — validação end-to-end
   - Roteiro em terminais paralelos
   - Critérios objetivos de sucesso
   - Validação opcional de tracing

---

## 📊 Snapshot da Plataforma

| Área | Estado atual |
|---|---|
| Runtime | Django 5.2 / Python 3.12 |
| Persistência | PostgreSQL 16 via Docker Compose; SQLite como fallback |
| Interface | Dashboard server-rendered com HTMX e Chart.js |
| Fontes de telemetria | Simulador determinístico, Modbus TCP, OPC-UA |
| Idempotência | `UniqueConstraint(sensor, timestamp)` + `bulk_create(ignore_conflicts=True)` |
| Observabilidade | OpenTelemetry com Jaeger, opt-in via `OTEL_ENABLED` |
| Validação | 73 testes automatizados + manual end-to-end |

<p align="center">
  <img src="assets/dashboard_mockup.png" alt="Dashboard LabTelemetry" width="92%">
</p>

---

## 🎯 Escopo desta Wiki

Cobre exclusivamente o projeto público. Planejamento interno, histórico de sessão e notas privadas ficam fora.

---

## 🛠️ Como Atualizar esta Wiki no GitHub

A wiki é um repositório git próprio, separado do repositório de código:

```bash
git clone https://github.com/Roberton003/labtelemetry.wiki.git /tmp/labtelemetry-wiki
cd /tmp/labtelemetry-wiki
# editar as páginas .md
git add -A && git commit -m "docs: atualiza wiki" && git push
```

No repositório de código, as páginas-fonte vivem em `docs/wiki-seed/` e são publicadas por `scripts/publish_wiki.sh` — edite lá para manter as duas cópias em sincronia.
