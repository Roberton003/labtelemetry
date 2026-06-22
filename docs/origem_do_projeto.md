# Origem Do Projeto LabTelemetry

O LabTelemetry nasceu como um projeto de portfólio para demonstrar, de forma concreta, a convergencia entre automacao industrial e engenharia de dados.

## Origem E Intencao

Os primeiros rascunhos do projeto mostravam uma intencao consistente:

- transformar experiencia de campo OT em software demonstravel;
- simular telemetria industrial com sensores, CLP e protocolos como ModbusTCP;
- tratar qualidade de dado como requisito central, nao como detalhe posterior;
- expor os dados por uma camada web simples, util e visual;
- registrar alertas e desvios de forma operacional;
- usar o projeto como prova tecnica de integracao OT/IT.

## Diretivas Que Vieram Dos Rascunhos

1. O projeto deve ser pequeno o suficiente para ser concluido, mas fiel ao dominio industrial.
2. A stack inicial deve permanecer enxuta: Django, PostgreSQL, Docker, Chart.js e Alpine.js.
3. A ordem correta de construcao e: modelo, simulador, qualidade, API, dashboard, observabilidade.
4. O valor do projeto esta em telemetria, calibracao, drift, alertas e series temporais.
5. Funcionalidades de plataforma mais amplas so entram se apoiarem a prova tecnica principal.

## O Que O Projeto Nao E

- nao e um produto SaaS generico;
- nao e um projeto de big data abstrato;
- nao e uma plataforma para acumular tecnologias sem necessidade;
- nao e um repositório de anotações soltas.

## Relação Com O Estado Atual

O plano atual do LabTelemetry continua coerente com esta origem quando:

- prioriza reprodutibilidade;
- externaliza configuracao sensivel;
- valida dados antes de exibir dashboards;
- adiciona PostgreSQL e observabilidade sem mudar o foco do dominio;
- evita dependencias e stacks que nao agregam valor direto ao caso de uso.

