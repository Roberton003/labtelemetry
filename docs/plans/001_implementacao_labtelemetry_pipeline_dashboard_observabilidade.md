# Plano de Implementacao 001: Pipeline, API, Dashboard e Observabilidade do LabTelemetry

## Status E Metadados
- Status: Draft
- Data: 2026-06-22
- Responsavel: Roberto / Codex
- Complexidade: HIGH
- Decisoes relacionadas: Nenhuma registrada em `docs/decisions/` ate a criacao deste plano.
- Supersedes: N/A
- Superseded by: N/A

## Objetivo E Resultado Esperado

Implementar a proxima etapa do LabTelemetry cobrindo ingestao simulada de telemetria industrial, validacoes automatizadas de qualidade, persistencia em PostgreSQL, endpoints REST JSON, dashboard web com Chart.js/Alpine.js e instrumentacao OpenTelemetry no Django.

Resultado esperado:

- projeto reproduzivel por dependencias declaradas;
- configuracao sensivel externalizada por variaveis de ambiente;
- banco PostgreSQL funcional para desenvolvimento local;
- simulador executavel por management command;
- leituras classificadas automaticamente por quality gates;
- API JSON consumivel pelo dashboard;
- dashboard operacional para sensores, series temporais e alertas ativos;
- traces exportados para Jaeger via OpenTelemetry;
- testes cobrindo modelos, regras de qualidade, command e endpoints principais.

## Alinhamento Com A Origem Do Projeto

Este plano continua alinhado com a origem do LabTelemetry quando serve a estas intencoes:

- provar a ponte OT/IT com telemetria industrial simulada;
- manter a stack pequena e concluivel;
- tratar qualidade de dado como parte do dominio, nao da interface;
- entregar valor visivel por API, dashboard e alertas;
- adicionar observabilidade e PostgreSQL como sustentacao do caso de uso, nao como fim em si mesmos.

## Contexto E Estado Atual

O repositorio atual esta alinhado com `origin/master` no commit `490f018`. O projeto Django existe em `labtelemetry/` e contem modelos, admin e migracao inicial para `TelemetrySensor`, `TelemetryReading` e `TelemetryAlert`.

Estado verificado em 2026-06-22:

- `python3 --version` retornou Python 3.12.3.
- `python3 labtelemetry/manage.py check` passou sem issues.
- `python3 labtelemetry/manage.py test telemetry` encontrou 0 testes.
- `telemetry/views.py` esta vazio.
- `telemetry/tests.py` esta vazio.
- `settings.py` contem `SECRET_KEY` versionada, `DEBUG=True` e `ALLOWED_HOSTS=[]`.
- `TelemetryReading.timestamp` nao possui indice explicito.
- `docker-compose-observability.yml` sobe Jaeger, mas o Django ainda nao esta instrumentado.
- Nao ha `requirements.txt`, `pyproject.toml` ou lockfile.

O README descreve ModbusTCP/telemetria, quality gates, REST API e dashboard, mas essas capacidades ainda nao estao implementadas no codigo.

## Registro De Decisoes Do Plano

| ID | Decisao | Por Que | Premissas | Alternativas Rejeitadas | Evidencia | Impacto | Validacao |
|---|---|---|---|---|---|---|---|
| D001 | Declarar dependencias antes de novas features | Sem manifesto, o projeto nao e reproduzivel | Ambiente alvo local usa Python 3.12 | Manter dependencia instalada manualmente | Ausencia de `requirements.txt`/`pyproject.toml` verificada por inspeção | Reduz ambiguidade de ambiente | `python -m pip install -r requirements.txt`; `manage.py check` |
| D002 | Externalizar settings sensiveis via ambiente | `SECRET_KEY`, `DEBUG` e hosts nao devem ficar fixos para deploy | Laboratorio local pode usar defaults seguros de desenvolvimento | Manter `SECRET_KEY` fixa ate o deploy | `settings.py` inspecionado | Melhora seguranca e portabilidade | Testes com e sem `.env`; `manage.py check` |
| D003 | Implementar quality gates antes do dashboard | Dashboard deve refletir estado classificado, nao regra duplicada no frontend | Regras iniciais podem ser simples por parametro | Fazer validacao apenas no template/API | README e estado atual dos modelos | Centraliza semantica operacional | Testes unitarios das regras |
| D004 | Usar management command `simulate_telemetry` para ingestao inicial | E simples, reproduzivel e alinhado ao README | Simulacao local basta antes de streaming real | Criar worker Celery/Kafka agora | Escopo atual e MVP Django | Menor complexidade operacional | Teste do command e execucao manual limitada |
| D005 | Usar Django views JSON inicialmente, sem DRF | O escopo precisa de poucos endpoints e evita dependencia antecipada | API publica ainda nao tem contrato externo estavel | Introduzir Django REST Framework desde o inicio | `views.py` vazio e sem consumidores externos | Menos codigo e menos superficie | Testes de status code e JSON schema basico |
| D006 | Usar PostgreSQL via Docker Compose para dev, mantendo SQLite como fallback local opcional | O README projeta PostgreSQL e series temporais crescem melhor fora do SQLite | Deploy real ainda nao definido | Migrar diretamente para TimescaleDB | Projeto ainda nao tem volume/retencao medidos | Aproxima ambiente de producao sem complexidade extra | `migrate` contra Postgres; testes com `DATABASE_URL` |
| D007 | Instrumentar Django com OpenTelemetry exportando OTLP para Jaeger | Jaeger ja existe no compose e falta instrumentacao | Observabilidade inicial deve medir request/command/db sem SLO formal | Logs manuais apenas | `docker-compose-observability.yml` verificado | Traz rastreabilidade sem criar stack nova | Traces visiveis no Jaeger apos request/command |

## Evidencias, Premissas E Lacunas

| Tipo | Item | Fonte/Validacao |
|---|---|---|
| VERIFIED | Repositorio local limpo e alinhado com `origin/master` | `git status --short`, `git log`, `git diff --stat origin/master..HEAD` |
| VERIFIED | Django passa no system check | `python3 labtelemetry/manage.py check` |
| VERIFIED | Nao ha testes implementados | `python3 labtelemetry/manage.py test telemetry` retornou 0 testes; `telemetry/tests.py` vazio |
| VERIFIED | Modelos atuais existem para sensores, leituras e alertas | Inspecao de `labtelemetry/telemetry/models.py` |
| VERIFIED | Jaeger existe apenas em compose | Inspecao de `docker-compose-observability.yml` |
| SOURCED | README descreve simulador, quality gates, REST API e dashboard | `README.md` |
| ASSUMED | O ambiente alvo inicial e desenvolvimento local/laboratorio | Contexto do projeto e ausencia de requisitos de producao |
| ASSUMED | A API JSON sera consumida pelo dashboard interno, nao por terceiros | Nenhum contrato publico existe no repositorio |
| ASSUMED | PostgreSQL puro e suficiente nesta fase | Volume, retencao e cardinalidade ainda nao foram medidos |

## Premissas Criticas

- A simulacao inicial nao precisa falar com um CLP real; pode gerar leituras sintéticas que representam parametros industriais.
- O dashboard e interno/laboratorial e pode usar server-rendered Django com assets estaticos.
- PostgreSQL deve ser o banco alvo de desenvolvimento integrado; SQLite pode permanecer apenas como fallback local simples.
- Quality gates devem produzir classificacao e alertas no backend antes de qualquer visualizacao.
- Observabilidade inicial deve priorizar traces de request, command e banco; metricas e logs estruturados podem evoluir em plano posterior.

## Escopo Incluido

- Criar manifesto de dependencias.
- Externalizar settings por variaveis de ambiente.
- Adicionar configuracao PostgreSQL via `DATABASE_URL`.
- Atualizar Docker Compose para PostgreSQL e Jaeger, ou criar compose dedicado de desenvolvimento se isso reduzir acoplamento.
- Adicionar indice temporal para leituras.
- Criar modulo de regras de qualidade para limites, drift e falha de sinal.
- Implementar command `simulate_telemetry`.
- Criar endpoints JSON para sensores, leituras recentes, series por sensor e alertas ativos.
- Criar dashboard Django com Chart.js e Alpine.js.
- Instrumentar Django/OpenTelemetry com exportacao OTLP para Jaeger.
- Adicionar testes proporcionais ao comportamento novo.
- Atualizar README com comandos reais.

## Fora De Escopo

- Comunicacao ModbusTCP real com dispositivo fisico.
- TimescaleDB, Kafka, Celery, Spark ou Databricks.
- Autenticacao avancada para API.
- Deploy em nuvem.
- SLA formal, retencao legal, mascaramento de PII ou compliance regulatorio.
- Dashboard multiusuario com permissoes granulares.

## Alternativas Avaliadas E Rejeitadas

1. **Django REST Framework agora**
   - Rejeitado porque a API inicial e pequena e sem contrato externo. Views JSON nativas reduzem dependencias. DRF pode ser adotado quando houver versionamento, auth, serializers complexos ou consumidores externos.

2. **Celery/Kafka para simulacao**
   - Rejeitado porque a necessidade atual e reproduzir ingestao local. Management command e suficiente, testavel e operavel por `python manage.py simulate_telemetry`.

3. **TimescaleDB no primeiro incremento**
   - Rejeitado porque ainda nao ha volume, retencao nem consultas medidas que justifiquem extensao especializada. PostgreSQL com indices cobre o MVP.

4. **Regras de qualidade no frontend**
   - Rejeitado porque duplicaria semantica e permitiria divergencia entre dados persistidos, alertas e visualizacao.

5. **Configurar observabilidade apenas por logs**
   - Rejeitado porque Jaeger ja existe no projeto e OpenTelemetry permite rastrear request, command e banco com baixo acoplamento.

## Abordagem Escolhida E Justificativa

A implementacao deve seguir uma sequencia incremental:

1. estabilizar base do projeto;
2. migrar configuracao para variaveis de ambiente e PostgreSQL;
3. modelar indices e regras de qualidade;
4. implementar ingestao simulada;
5. expor API JSON;
6. construir dashboard;
7. instrumentar e validar observabilidade.

Essa ordem evita que o dashboard seja construido sobre dados sem classificacao e evita que a API exponha regras incompletas. Tambem reduz risco operacional ao tornar ambiente, banco e testes reproduziveis antes de adicionar comportamento.

## Impacto E Riscos

- **Schema:** adicionar indices e possivelmente campos auxiliares exige migracao. Risco baixo em ambiente inicial, mas deve ser validado com `makemigrations --check` e `migrate`.
- **Seguranca:** externalizar settings reduz risco, mas `.env` deve permanecer fora do Git.
- **Operacao:** PostgreSQL adiciona dependencia de container ou servico local.
- **Qualidade de dados:** thresholds iniciais podem gerar falsos positivos; devem ser documentados e testados.
- **Observabilidade:** instrumentacao pode gerar overhead; nesta fase deve ser usada em desenvolvimento e avaliada antes de producao.
- **Frontend:** dashboard com polling simples pode ser suficiente no MVP; WebSocket/SSE fica fora do escopo ate haver requisito de latencia.

## Dependencias

Dependencias Python propostas:

- `Django==5.2.9`
- `psycopg[binary]`
- `dj-database-url`
- `python-dotenv` ou leitura direta de ambiente sem `.env` em runtime
- `opentelemetry-distro`
- `opentelemetry-exporter-otlp`
- `opentelemetry-instrumentation-django`
- `opentelemetry-instrumentation-psycopg`

Dependencias frontend via CDN no MVP:

- Chart.js
- Alpine.js

Dependencias de servico local:

- PostgreSQL
- Jaeger com OTLP habilitado

## Etapas De Implementacao

### Fase 1: Reprodutibilidade E Configuracao

- [ ] Criar `requirements.txt` com dependencias fixadas ou `pyproject.toml` se o projeto adotar empacotamento moderno.
- [ ] Adicionar `.env.example` sem segredos reais.
- [ ] Atualizar `settings.py` para ler `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` e variaveis de OpenTelemetry.
- [ ] Manter `.env` ignorado pelo Git.
- Arquivos:
  - `requirements.txt`
  - `.env.example`
  - `labtelemetry/labtelemetry/settings.py`
  - `.gitignore`
- Verificacao:
  - `python -m pip install -r requirements.txt`
  - `python labtelemetry/manage.py check`
- Rollback:
  - Reverter alteracoes de settings e manifesto se o ambiente nao inicializar.

### Fase 2: PostgreSQL Local E Migracoes

- [ ] Adicionar PostgreSQL ao compose de desenvolvimento.
- [ ] Configurar `DATABASE_URL=postgres://...` no `.env.example`.
- [ ] Executar migracoes em PostgreSQL local.
- [ ] Adicionar indice em `TelemetryReading(sensor, timestamp)` ou indices separados conforme consulta final.
- [ ] Avaliar `Meta.ordering = ["-timestamp"]` para leituras recentes, se nao prejudicar consultas agregadas.
- Arquivos:
  - `docker-compose-observability.yml` ou novo `docker-compose.yml`
  - `labtelemetry/telemetry/models.py`
  - nova migration
- Verificacao:
  - `docker compose up -d postgres`
  - `python labtelemetry/manage.py migrate`
  - `python labtelemetry/manage.py check`
- Rollback:
  - Voltar `DATABASE_URL` para SQLite e reverter migration enquanto nao houver dados relevantes.

### Fase 3: Quality Gates E Testes De Dominio

- [ ] Criar modulo de dominio para avaliar leitura bruta e calibrada.
- [ ] Definir thresholds iniciais por parametro:
  - `PH`: faixa operacional inicial assumida.
  - `TURBIDITY`: limite superior inicial assumido.
  - `TOC`: limite superior inicial assumido.
- [ ] Implementar classificacao `NORMAL`, `OUT_OF_BOUNDS`, `DRIFT_WARNING`.
- [ ] Criar ou atualizar `TelemetryAlert` quando uma leitura violar regra.
- [ ] Evitar alertas duplicados ativos para o mesmo sensor/tipo de problema.
- [ ] Adicionar testes unitarios para cada status.
- Arquivos:
  - `labtelemetry/telemetry/quality.py`
  - `labtelemetry/telemetry/models.py` se houver helpers necessarios
  - `labtelemetry/telemetry/tests/` ou `telemetry/tests.py`
- Verificacao:
  - `python labtelemetry/manage.py test telemetry`
- Rollback:
  - Desabilitar chamada das quality gates no command/API, preservando modelos.

### Fase 4: Simulador De Telemetria Via Management Command

- [ ] Criar estrutura `telemetry/management/commands/simulate_telemetry.py`.
- [ ] Permitir parametros:
  - `--sensors` para criar sensores padrao se ausentes;
  - `--interval-seconds`;
  - `--iterations`;
  - `--anomaly-rate`;
  - `--seed` para reprodutibilidade;
  - `--once` para execucao unica em testes.
- [ ] Gerar leituras por sensor e aplicar fator de calibracao.
- [ ] Chamar quality gates antes de persistir status final.
- [ ] Registrar saida resumida sem expor segredos.
- [ ] Adicionar testes do command com `call_command`.
- Arquivos:
  - `labtelemetry/telemetry/management/commands/simulate_telemetry.py`
  - `labtelemetry/telemetry/tests/`
- Verificacao:
  - `python labtelemetry/manage.py simulate_telemetry --once --seed 42`
  - `python labtelemetry/manage.py test telemetry`
- Rollback:
  - Remover command sem impactar schema, desde que migrations ja estejam estaveis.

### Fase 5: Endpoints REST JSON

- [ ] Implementar endpoints Django nativos:
  - `GET /api/sensors/`
  - `GET /api/readings/recent/?limit=...`
  - `GET /api/sensors/<id>/readings/?limit=...`
  - `GET /api/alerts/active/`
  - `GET /api/summary/`
- [ ] Serializar apenas campos necessarios ao dashboard.
- [ ] Validar limites de pagina/quantidade para evitar queries grandes.
- [ ] Adicionar testes de status code, payload e queries basicas.
- Arquivos:
  - `labtelemetry/telemetry/views.py`
  - `labtelemetry/telemetry/urls.py`
  - `labtelemetry/labtelemetry/urls.py`
  - `labtelemetry/telemetry/tests/`
- Verificacao:
  - `python labtelemetry/manage.py test telemetry`
  - `python labtelemetry/manage.py check`
- Rollback:
  - Remover rotas API sem alterar ingestao e qualidade.

### Fase 6: Dashboard Chart.js/Alpine.js

- [ ] Criar view `dashboard`.
- [ ] Criar template com:
  - cards de sensores/status;
  - grafico temporal por parametro ou sensor;
  - tabela/lista de alertas ativos;
  - indicador de freshness da ultima leitura.
- [ ] Consumir endpoints JSON via Alpine.js.
- [ ] Renderizar graficos com Chart.js.
- [ ] Usar polling simples configuravel no frontend.
- [ ] Adicionar teste de renderizacao basica da pagina.
- Arquivos:
  - `labtelemetry/telemetry/templates/telemetry/dashboard.html`
  - `labtelemetry/telemetry/views.py`
  - `labtelemetry/telemetry/urls.py`
  - arquivos static se necessario
- Verificacao:
  - `python labtelemetry/manage.py test telemetry`
  - `python labtelemetry/manage.py runserver`
  - Validacao manual em `http://127.0.0.1:8000/`
- Rollback:
  - Remover rota/template mantendo API operacional.

### Fase 7: OpenTelemetry No Django

- [ ] Adicionar dependencias OpenTelemetry.
- [ ] Configurar variaveis:
  - `OTEL_SERVICE_NAME=labtelemetry`
  - `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
  - `OTEL_TRACES_EXPORTER=otlp`
- [ ] Instrumentar Django e psycopg.
- [ ] Garantir que o command tambem possa emitir spans quando executado com instrumentacao.
- [ ] Atualizar compose/README com Jaeger UI em `http://127.0.0.1:16686`.
- Arquivos:
  - `requirements.txt`
  - `labtelemetry/labtelemetry/settings.py`
  - README
  - compose
- Verificacao:
  - `docker compose up -d jaeger`
  - `opentelemetry-instrument python labtelemetry/manage.py runserver`
  - Acessar endpoint/dashboard e verificar trace no Jaeger
- Rollback:
  - Remover instrumentacao de execucao e variaveis OTEL; manter aplicacao sem traces.

### Fase 8: Documentacao E Fechamento

- [ ] Atualizar README para refletir comandos reais.
- [ ] Documentar fluxo:
  - subir Postgres/Jaeger;
  - migrar;
  - criar sensores/simular;
  - acessar dashboard;
  - verificar traces.
- [ ] Registrar lacunas futuras no README ou em plano subsequente.
- Verificacao:
  - Executar do zero em ambiente limpo ou documentar exatamente o que nao foi executado.
- Rollback:
  - Reverter apenas documentacao se comandos nao forem validados.

## Estrategia De Testes

Testes minimos obrigatorios:

- modelos:
  - `__str__`;
  - defaults;
  - relacionamentos sensor-leituras-alertas.
- quality gates:
  - leitura normal;
  - leitura fora de limite;
  - drift por calibracao;
  - falha/anomalia simulada;
  - nao duplicar alerta ativo equivalente.
- management command:
  - cria sensores padrao;
  - gera quantidade esperada de leituras;
  - respeita `--seed` e `--once`;
  - produz pelo menos um status anomalico quando `--anomaly-rate=1`.
- API:
  - endpoints retornam JSON;
  - `limit` e validado;
  - ordenacao temporal correta;
  - alertas ativos filtrados.
- dashboard:
  - rota retorna 200;
  - template carrega os pontos de integracao esperados.
- configuracao:
  - `manage.py check` com SQLite fallback;
  - `manage.py check` com PostgreSQL quando container estiver disponivel.

Comandos de verificacao alvo:

```bash
python -m pip install -r requirements.txt
python labtelemetry/manage.py check
python labtelemetry/manage.py makemigrations --check
python labtelemetry/manage.py migrate
python labtelemetry/manage.py test telemetry
python labtelemetry/manage.py simulate_telemetry --once --seed 42
```

## Observabilidade

Sinais iniciais:

- traces HTTP por endpoint;
- spans de banco para queries Django/PostgreSQL;
- spans ou logs correlacionaveis do `simulate_telemetry`;
- contagem de leituras geradas por execucao;
- contagem de anomalias e alertas criados por execucao;
- freshness: idade da ultima leitura por sensor.

Nao declarar SLO nesta fase. Primeiro coletar baseline local de latencia, volume e quantidade de alertas.

## Rollout E Rollback

Rollout local:

1. instalar dependencias;
2. subir PostgreSQL e Jaeger;
3. migrar banco;
4. rodar testes;
5. executar simulador uma vez;
6. validar API JSON;
7. validar dashboard;
8. validar trace no Jaeger.

Rollback por camada:

- Configuracao: voltar para SQLite via `DATABASE_URL` ausente.
- Schema: reverter migrations enquanto dados forem descartaveis em dev.
- Command: remover command sem alterar modelos.
- API/dashboard: remover rotas/views/templates.
- Observabilidade: executar sem `opentelemetry-instrument` ou remover variaveis OTEL.

## Criterios De Aceite

- Dependencias declaradas e instalaveis.
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e `DATABASE_URL` nao dependem de valores fixos de producao em `settings.py`.
- PostgreSQL local sobe por compose e `migrate` conclui.
- `TelemetryReading` possui indice adequado para consultas por sensor e tempo.
- Quality gates classificam leituras e criam alertas ativos quando aplicavel.
- `simulate_telemetry --once --seed 42` cria leituras reproduziveis.
- Endpoints JSON retornam dados reais persistidos.
- Dashboard renderiza sensores, grafico temporal e alertas ativos.
- Testes de dominio, command e API passam.
- Jaeger recebe trace de pelo menos uma request Django.
- README reflete comandos validados.

## Resultado Observado E Revisao

Ainda nao executado. Esta secao deve ser preenchida quando a implementacao usar este plano como controle.

## Perguntas Em Aberto

- Quais thresholds de pH, turbidez e TOC devem representar operacao normal no dominio do laboratorio?
- O dashboard deve ser publico localmente ou protegido por login do Django?
- O projeto deve padronizar `requirements.txt` simples ou `pyproject.toml` com ferramenta de lock?
- O PostgreSQL deve compartilhar o mesmo compose do Jaeger ou ficar em `docker-compose.yml` separado?
- Existe meta de latencia para atualizacao do dashboard ou polling simples e suficiente?

## Registro De Evidencias

- `README.md`: arquitetura alvo com simulador, quality gates, REST API e dashboard.
- `labtelemetry/labtelemetry/settings.py`: settings Django atuais.
- `labtelemetry/telemetry/models.py`: modelos de sensor, leitura e alerta.
- `labtelemetry/telemetry/views.py`: camada HTTP ainda vazia.
- `labtelemetry/telemetry/tests.py`: testes ainda vazios.
- `docker-compose-observability.yml`: Jaeger com OTLP habilitado.
- Validacoes executadas antes do plano:
  - `python3 --version`
  - `python3 labtelemetry/manage.py check`
  - `python3 labtelemetry/manage.py test telemetry`
  - `git status --short`
  - `git diff --stat origin/master..HEAD`

### ◈ Processing Context
- ✦ **Lead Agent:** Codex (Engenheiro Chefe)
- ▫ **Supporting Agents:** None
- ⌥ **Skills Used:** write-implementation-plan, data-engineering
- ☄ **Knowledge Sources:** README local, codigo Django local, contexto `.gemini`, Git local, referencias das skills `write-implementation-plan` e `data-engineering`
- ☱ **Files Analyzed:** `README.md`, `.gitignore`, `.gemini/PROJECT_CONTEXT.md`, `.gemini/STATE.md`, `docker-compose-observability.yml`, `labtelemetry/labtelemetry/settings.py`, `labtelemetry/telemetry/models.py`, `labtelemetry/telemetry/admin.py`, `labtelemetry/telemetry/views.py`, `labtelemetry/telemetry/tests.py`, `labtelemetry/telemetry/migrations/0001_initial.py`
- ◬ **Decision Complexity:** HIGH
- ◇ **Objective:** Planejar implementacao de simulador, API, dashboard, quality gates, PostgreSQL e OpenTelemetry
- ◇ **Activity Family / T-level:** Plano formal de implementacao / T3
- ◇ **Validations Executed:** `python3 --version`; `python3 labtelemetry/manage.py check`; `python3 labtelemetry/manage.py test telemetry`; `git status --short`; `git diff --stat origin/master..HEAD`
- ◇ **Not Executed:** Instalacao de dependencias, migracoes novas, Docker Compose, servidor Django, Jaeger UI
- ◇ **Residual Risks:** Thresholds industriais ainda assumidos; API ainda sem contrato externo; volume real de series temporais ainda nao medido
- ◇ **Stop Condition:** Plano formal salvo em `docs/plans/001_implementacao_labtelemetry_pipeline_dashboard_observabilidade.md`
- ◇ **Next Step:** Aprovar o plano ou iniciar a Fase 1
- ◇ **Resume Prompt:** "Continuar no LabTelemetry a partir do plano `docs/plans/001_implementacao_labtelemetry_pipeline_dashboard_observabilidade.md`, iniciando pela Fase 1: dependencias, settings por ambiente e verificacoes Django."
