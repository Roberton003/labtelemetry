# PRD 001: LabTelemetry OT/IT Dashboard

## Status E Metadados

- Status: Draft
- Data: 2026-06-22
- Responsavel: Roberto / Codex
- Produto: LabTelemetry
- Escopo: MVP de telemetria industrial simulada, qualidade de dados, API e dashboard
- Fontes relacionadas:
  - `docs/origem_do_projeto.md`
  - `docs/plans/001_implementacao_labtelemetry_pipeline_dashboard_observabilidade.md`
  - `apendices/PLANO_OPERACIONAL_LABTELEMETRY.md`
  - `apendices/PLANO_CURSO_PROJETO_IOT.md`
  - `apendices/FUNDAMENTOS_TEORICOS_OT_IT.md`

## Problema

Projetos de engenharia de dados muitas vezes demonstram ferramentas, mas nao demonstram entendimento do dado na origem. O LabTelemetry resolve esse problema criando um produto demonstravel de integracao OT/IT: sensores industriais simulados geram series temporais, o backend classifica a qualidade desses dados, alertas sao registrados e uma interface web mostra o estado operacional.

O objetivo nao e construir uma plataforma generica de big data. O objetivo e provar, com codigo funcional, a ponte entre automacao industrial e engenharia de dados.

## Objetivos Do Produto

1. Simular leituras industriais realistas para pH, turbidez e TOC.
2. Persistir series temporais com metadados de sensor, calibracao e status de qualidade.
3. Detectar anomalias basicas como fora de limite, drift e falha de sinal.
4. Registrar alertas operacionais ativos.
5. Expor dados por endpoints JSON consumiveis por interface web.
6. Exibir dashboard operacional com sensores, historico recente e alertas.
7. Tornar o ambiente reproduzivel com dependencias, configuracao e banco local.
8. Instrumentar o backend para rastreabilidade inicial com OpenTelemetry.

## Nao Objetivos

- Conectar a CLP fisico real nesta etapa.
- Implementar streaming distribuido com Kafka, Spark, Airflow ou Databricks.
- Criar produto SaaS multiusuario.
- Substituir um historiador industrial real como AVEVA PI System.
- Resolver compliance regulatorio ou seguranca OT real de producao.
- Criar dashboard executivo generico sem relacao com telemetria operacional.

## Usuarios E Personas

### Engenheiro De Dados Industrial

Precisa demonstrar que consegue transformar sinais de automacao em dados confiaveis, consultaveis e observaveis.

### Analista/Operador De Processo

Precisa ver rapidamente quais sensores estao saudaveis, quais leituras estao fora do esperado e quais alertas estao ativos.

### Recrutador Tecnico Ou Avaliador De Portfólio

Precisa conseguir rodar o projeto, entender a arquitetura e verificar que existe codigo funcional, nao apenas documentacao.

## Jornada Principal

1. O avaliador sobe o ambiente local.
2. O sistema aplica migracoes e disponibiliza sensores.
3. O simulador gera leituras de telemetria.
4. O backend aplica calibracao e quality gates.
5. Leituras e alertas sao persistidos.
6. A API retorna sensores, leituras recentes e alertas ativos.
7. O dashboard exibe o estado operacional em tempo quase real.
8. O avaliador consulta traces basicos no Jaeger quando observabilidade estiver habilitada.

## Requisitos Funcionais

### RF001: Cadastro De Sensores

O sistema deve manter sensores com nome, parametro medido, status operacional e fator de calibracao.

Critérios de aceite:

- sensores suportam pelo menos `PH`, `TURBIDITY` e `TOC`;
- sensores possuem status `HEALTHY`, `DRIFTING` ou `FAILED`;
- sensores podem ser consultados via admin e API.

### RF002: Ingestao Simulada

O sistema deve fornecer um management command para gerar leituras sinteticas.

Critérios de aceite:

- comando executa uma rodada unica para teste;
- comando executa multiplas iteracoes com intervalo configuravel;
- comando permite seed para reproducibilidade;
- comando cria leituras associadas a sensores existentes ou padrao.

### RF003: Calibracao E Quality Gates

O sistema deve aplicar fator de calibracao e classificar a leitura antes da exibicao.

Critérios de aceite:

- leitura normal recebe status `NORMAL`;
- leitura fora dos limites recebe `OUT_OF_BOUNDS`;
- leitura com indicio de drift recebe `DRIFT_WARNING`;
- regras ficam no backend, nao no frontend.

### RF004: Alertas Operacionais

O sistema deve registrar alerta quando uma regra critica for violada.

Critérios de aceite:

- alertas possuem sensor, mensagem, status ativo e timestamp;
- alertas ativos podem ser consultados por API;
- o sistema evita duplicacao desnecessaria de alerta ativo para o mesmo problema.

### RF005: API JSON

O sistema deve expor endpoints JSON para consumo do dashboard.

Critérios de aceite:

- endpoint lista sensores e status;
- endpoint retorna leituras recentes;
- endpoint retorna leituras por sensor;
- endpoint retorna alertas ativos;
- endpoint de resumo retorna indicadores basicos.

### RF006: Dashboard Operacional

O sistema deve exibir uma interface web para monitorar o estado dos sensores.

Critérios de aceite:

- dashboard mostra cards ou indicadores de sensores;
- dashboard mostra grafico temporal recente;
- dashboard mostra alertas ativos;
- dashboard atualiza dados via chamadas JSON ou polling simples.

### RF007: Reprodutibilidade

O sistema deve ser executavel por outro avaliador sem depender de configuracao manual oculta.

Critérios de aceite:

- dependencias declaradas;
- `.env.example` documenta variaveis esperadas;
- README explica comandos validados;
- banco local pode ser inicializado por migracoes.

### RF008: Observabilidade Inicial

O sistema deve permitir rastrear requests e operacoes basicas do backend.

Critérios de aceite:

- Jaeger sobe localmente;
- Django pode exportar traces por OTLP;
- README documenta como verificar a UI do Jaeger.

## Requisitos Nao Funcionais

- O MVP deve ser simples o suficiente para rodar localmente.
- O backend deve manter regras de qualidade em codigo testavel.
- Consultas de leitura devem considerar indice temporal por sensor.
- Segredos nao devem ficar fixos para uso fora de laboratorio local.
- O dashboard deve priorizar leitura operacional clara, nao marketing.
- O projeto deve preservar stack enxuta ate concluir o MVP.

## Dados E Dominio

Entidades principais:

- `TelemetrySensor`: instrumento ou ponto monitorado.
- `TelemetryReading`: evento temporal de leitura.
- `TelemetryAlert`: incidente operacional ou qualidade relevante.

Status principais:

- Sensor: `HEALTHY`, `DRIFTING`, `FAILED`.
- Leitura: `NORMAL`, `OUT_OF_BOUNDS`, `DRIFT_WARNING`.

Parametros iniciais:

- `PH`
- `TURBIDITY`
- `TOC`

## Indicadores De Sucesso

- O projeto roda localmente com comandos documentados.
- O simulador gera leituras persistidas.
- Quality gates classificam leituras com testes.
- API retorna JSON real vindo do banco.
- Dashboard exibe sensores, graficos e alertas.
- Pelo menos uma request gera trace quando observabilidade estiver habilitada.
- README comunica claramente o valor OT/IT do projeto.

## Fora De Escopo Para O MVP

- autenticacao e autorizacao completas;
- integracao com CLP real;
- OPC-UA real;
- deploy em nuvem;
- TimescaleDB;
- WebSocket/SSE;
- dashboards executivos complexos;
- data lakehouse, Spark ou orquestradores.

## Riscos E Premissas

| Tipo | Item | Tratamento |
|---|---|---|
| Risco | Escopo crescer para plataforma generica | Usar `docs/origem_do_projeto.md` como guardrail |
| Risco | Dashboard ser feito antes das regras de qualidade | Manter ordem: simulador, quality gates, API, dashboard |
| Risco | Thresholds industriais iniciais serem arbitrarios | Documentar valores como premissas e cobrir com testes |
| Risco | Observabilidade virar objetivo proprio | Limitar ao rastreamento basico de request, command e banco |
| Premissa | Simulacao sintetica basta para o MVP | Validar com command reproduzivel e dados plausiveis |
| Premissa | PostgreSQL puro atende a etapa atual | Reavaliar TimescaleDB somente com volume medido |

## Relação Com O Plano De Implementacao

Este PRD define o problema, usuarios, objetivos e requisitos do produto. O plano `docs/plans/001_implementacao_labtelemetry_pipeline_dashboard_observabilidade.md` define a ordem tecnica de execucao.

Quando houver conflito, usar esta ordem:

1. `docs/origem_do_projeto.md` para intencao e limites do projeto;
2. este PRD para escopo e requisitos;
3. plano de implementacao para sequencia tecnica;
4. codigo e testes como fonte final do estado executavel.

## Perguntas Em Aberto

- Quais faixas iniciais de pH, turbidez e TOC representam operacao normal?
- O dashboard deve exigir login no MVP ou ficar aberto localmente?
- A API inicial deve permanecer em Django nativo ou adotar DRF antes de consumidores externos?
- O simulador deve chamar o command `simulate_telemetry` ou preservar o nome historico `simulate_sensors`?

