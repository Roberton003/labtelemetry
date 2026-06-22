# Fluxo De Review Do LabTelemetry

Este projeto usa um ciclo curto de implementacao e revisao inspirado no `claude-review-loop`.

## Objetivo

Garantir que cada mudanca relevante passe por duas etapas:

1. implementacao do cambio;
2. revisao independente do diff antes de aceitar a alteracao.

## Fluxo

1. Criar uma branch de trabalho a partir de `master`.
2. Implementar uma unidade pequena de valor.
3. Executar verificacoes locais relevantes.
4. Revisar o diff com uma segunda passada independente.
5. Corrigir apenas o que a revisao sustentar.
6. Reexecutar validacoes.
7. Commitar a unidade final.
8. Abrir PR com contexto, impacto e verificacoes executadas.

## Regras Praticas

- Cada PR deve corresponder a um objetivo pequeno e verificavel.
- Mudancas de docs, plano e codigo podem viver juntas apenas quando estiverem na mesma unidade de entrega.
- A revisao precisa olhar:
  - risco funcional;
  - risco de dados;
  - impacto em schema;
  - impacto em testes;
  - consistencia de documentacao.
- Nao aceitar mudanca sem um resultado claro de validacao.

## Como Isso Se Aplica Ao LabTelemetry

Para este projeto, a ordem correta e:

1. documentar a origem e o plano;
2. implementar configuracao e reprodutibilidade;
3. revisar o diff;
4. seguir para simulador, quality gates, API e dashboard em entregas separadas;
5. manter observabilidade e deploy como partes da mesma linha de entrega, nao como tarefas soltas.

## Resultado Esperado

Ao final de cada ciclo, deve existir:

- um commit pequeno;
- um diff revisado;
- uma verificacao executada;
- uma PR pronta para merge.

