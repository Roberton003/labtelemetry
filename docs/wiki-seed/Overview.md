[[Home]] | [[Overview]] | [[Architecture]] | [[Idempotencia-e-Replay]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# 📖 Visão Geral

LabTelemetry é um laboratório de telemetria OT/IT em Django. Ele adquire leituras de sensores industriais (reais ou simulados), persiste a série temporal, aplica regras de qualidade de processo, expõe endpoints JSON e renderiza um dashboard operacional.

---

## 🎯 Por Que Este Projeto Existe

**Problema:** a maioria dos projetos de dados demonstra ferramentas, não a forma que o dado tem **na origem**. Começam com um CSV limpo, quando o trabalho real começa num registrador Modbus de 16 bits, com sensor descalibrado e timestamp que às vezes vem da fonte e às vezes do coletor.

**Abordagem:** manter o sistema deliberadamente pequeno, para que o caminho da geração da telemetria até o consumo pela aplicação seja inteiramente visível, testável e reproduzível — sem introduzir plataforma distribuída antes de haver necessidade.

**Resultado:** cada decisão do pipeline cabe na cabeça de quem lê, e cada garantia tem um teste que a sustenta.

---

## ⚙️ Capacidades Principais

- **Aquisição multi-protocolo:** Modbus TCP, OPC-UA e simulador determinístico, intercambiáveis atrás da mesma abstração.
- **Domínio de processo:** pH, turbidez e TOC — parâmetros de tratamento de água, com limites e detecção de drift de calibração.
- **Qualidade como código:** regras de limite e desvio avaliadas no backend, não em query de dashboard.
- **Alertas operacionais** com supressão de duplicata por sensor e tipo.
- **API JSON** sob `/api/`, simples o suficiente para alimentar o dashboard diretamente.
- **Idempotência enforçada no banco** — ver [[Idempotencia-e-Replay]].
- **Tracing opcional** com OpenTelemetry e Jaeger, ligado por variável de ambiente.

---

## 🧭 Posicionamento Público

LabTelemetry se entende melhor como:

1. um laboratório OT/IT reproduzível
2. um projeto de portfólio com fluxo operacional real
3. um produto de dados compacto, com contrato explícito

---

## 🚫 Fora de Escopo

O que não está aqui, não está por decisão:

- **Processamento de stream distribuído** — o volume do lab não justifica; introduzir Kafka aqui demonstraria a ferramenta, não resolveria o problema.
- **Autenticação de produção na API** — o escopo é laboratório local.
- **Infraestrutura cloud multi-região.**
- **Exactly-once formal** — o comportamento real e seus limites estão documentados em [[Idempotencia-e-Replay]] em vez de prometidos.
