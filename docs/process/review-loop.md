# Fluxo De Review Do LabTelemetry

Este projeto usa um ciclo curto de implementacao e revisao baseado no principio `review-loop`.

## Objetivo

Garantir que cada mudanca relevante passe por duas etapas:

1. implementacao do cambio;
2. revisao independente do diff antes de aceitar a alteracao.

## Origem Da Skill

A skill local `review-loop` foi criada para transformar este principio em uma rotina reutilizavel do Codex. Ela vive fora do repositorio, em `/home/rob3rto88/.codex/skills/review-loop`, porque e uma capacidade operacional do agente e nao uma dependencia runtime do LabTelemetry.

O repositorio registra apenas o proposito e as regras de uso, para que o fluxo continue compreensivel por qualquer pessoa revisando o projeto.

## Proposito

O `review-loop` existe para reduzir risco antes de aceitar mudancas. Ele força uma segunda passada sobre o diff, separando implementacao de revisao e evitando que uma entrega seja aceita apenas porque "funcionou localmente".

No LabTelemetry, a revisao deve procurar especialmente:

- regressao funcional;
- risco de dados ou schema;
- falta de testes proporcionais;
- vazamento de segredo ou configuracao insegura;
- divergencia entre README, PRD, plano e codigo;
- mudanca que empurre o projeto para fora do escopo OT/IT definido.

## Fluxo

1. Criar uma branch de trabalho a partir de `master`.
2. Implementar uma unidade pequena de valor.
3. Executar verificacoes locais relevantes.
4. Revisar o diff com uma segunda passada independente.
5. Corrigir apenas o que a revisao sustentar.
6. Reexecutar validacoes.
7. Commitar a unidade final.
8. Abrir PR com contexto, impacto e verificacoes executadas.

## Papel Do Subagente/Revisor

Para mudancas pequenas, a revisao pode ser uma segunda passada do Lead Agent.

Para mudancas de risco maior, acionar um subagente ou revisor independente com escopo limitado:

- entrada: objetivo da mudanca, diff, comandos executados e arquivos afetados;
- foco: bugs, riscos, testes ausentes, schema, seguranca e documentacao;
- saida: achados acionaveis com severidade e referencia de arquivo;
- restricao: nao receber a resposta desejada nem conclusoes prontas.

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

## PR, PRD E Historico De Commits

`PR` e o Pull Request do GitHub: ele entrega uma unidade revisavel de mudanca.

`PRD` e o Product Requirements Document: ele descreve problema, usuarios, objetivos, requisitos e limites do produto.

No LabTelemetry, o PRD orienta o que deve ser construido; a PR entrega uma parte revisavel desse trabalho.

Se hooks locais criarem commits automaticos de checkpoint na branch, a correcao preferida antes de integrar no `master` e usar squash merge no GitHub. Assim o historico final fica limpo mesmo que a branch de trabalho contenha checkpoints intermediarios.

Quando houver necessidade de historico local limpo antes do push, criar uma branch nova a partir de `master` e cherry-pickar apenas os commits intencionais. Nao usar comandos destrutivos para limpar historico sem autorizacao explicita.

## Integracao Com O Harness OpenCode

Este workflow esta implementado como skill de orquestracao no OpenCode:

- **Skill:** `~/.config/opencode/skills/review-loop/SKILL.md`
- **Nome:** `review-loop`
- **Tipo:** Orquestrador leve — compoe skills existentes sem duplicar
- **Skills componentes:** `adversarial-review` (fidelidade plano→diff), `code-quality` (checklist de codigo), `verification-engineer` (execucao de testes)
- **Agentes de apoio:** `adversarial-reviewer`, `verification-engineer`, `security-reviewer`, `completion-auditor`

Para ativar: `skill("review-loop")` antes de ciclos T1-T3 no LabTelemetry.

Detalhes

https://github.com/hamelsmu/claude-review-loop