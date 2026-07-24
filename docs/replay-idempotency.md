# Replay, Deduplicação e Idempotência

## Contexto

O LabTelemetry não foi projetado com garantias formais de exactly-once.
Este documento explica o comportamento real do sistema para que avaliadores
entendam os trade-offs sem surpresas.

## Estado Atual

### Ingestão (`ingest_telemetry --once`)

Cada execução do comando `ingest_telemetry --once`:
1. Abre uma conexão com a fonte (`SimulatorAdapter` ou `ModbusTCPAdapter`)
2. Itera sobre as amostras fornecidas pela fonte
3. Para cada amostra, cria um `TelemetryReading` no banco

**Comportamento:** Não há verificação de duplicata. Se o mesmo comando for
executado duas vezes com o mesmo seed, serão criados registros duplicados
(com `id` diferente, mesmo `timestamp` e `raw_value`).

### Simulação (`simulate_telemetry --seed 42 --iterations N`)

Usa `seed` para gerar a mesma sequência de leituras, mas **não verifica**
se aquelas leituras já existem. Cada execução insere N novos registros.

## Como Replay Funciona (e Não Funciona)

### Cenário: Reproduzir uma falha

```bash
# Primeira execução — gera 10 leituras
simulate_telemetry --seed 42 --iterations 10 --anomaly-rate 0.3

# Segunda execução — gera OUTRAS 10 leituras (mesmo seed, mesmo valor)
simulate_telemetry --seed 42 --iterations 10 --anomaly-rate 0.3
# Resultado: 20 leituras no banco, as 10 primeiras duplicadas em valor
```

**Conclusão:** O seed garante **repetibilidade do valor**, não
**idempotência de inserção**.

### Cenário: Reprocessar um dia

Não há suporte a janela temporal de reprocessamento. O comando sempre
cria leituras "novas" com timestamp = agora.

## Deduplicação

**Não existe.** Não há índice único natural, hash ou upsert que impeça
duplicatas. A chave primária é `id` (auto-increment), que por definição
nunca colide.

### O que impede deduplicação total hoje

- `TelemetryReading` tem `UniqueConstraint(sensor, timestamp)`, o que
  impede duas leituras do mesmo sensor no mesmo instante, mas
  **não cobre** `raw_value` — leituras com mesmo sensor+timestamp mas
  valores diferentes ainda colidem (embora na prática isso dependa da
  precisão do timestamp)
- Django ORM não suporta `INSERT ... ON CONFLICT` sem raw SQL ou
  `get_or_create` (que adiciona SELECT antes de INSERT)
- Não há hash de payload ou identificador de fonte externa

## Idempotência Real no Sistema

Apesar da ingestão não ser idêntica, **algumas partes do sistema são
idempotentes por construção:**

| Componente | Idempotente? | Como |
|-----------|-------------|------|
| `quality.py: evaluate_and_alert()` | ✅ Sim | Se alerta ativo já existe para o mesmo problema, não recria |
| `GET /api/...` | ✅ Sim | REST GET é naturalmente idempotente |
| `migrate` | ✅ Sim | Django migrations são idempotentes |
| `UniqueConstraint(sensor, timestamp)` | ✅ Sim (parcial) | Impede duplicata exata mesmo sensor+timestamp; não cobre valores diferentes |
| `ingest_telemetry --once` | ❌ Não | Cada execução cria novas leituras (timestamps mudam) |
| `simulate_telemetry` | ❌ Não | Cada execução cria novas leituras (timestamps mudam) |

## O Que Mudaria para Idempotência Formal

Se o projeto evoluísse para exigir exactly-once:

1. **Unique constraint:** Adicionar `(sensor_id, timestamp, raw_value)` como
   unique → `INSERT ... ON CONFLICT DO NOTHING`
2. **Hash de payload:** `SHA256(raw_value + timestamp + sensor_id)` como
   chave natural
3. **Campo `source`:** Identificar origem para evitar colisão entre
   simulador e Modbus
4. **Janela de replay:** Permitir `--start-time` e `--end-time` no comando
   de ingestão

## Resumo

| Pergunta | Resposta |
|----------|----------|
| Posso executar o mesmo comando duas vezes? | Sim, mas cria duplicatas |
| Posso reproduzir a mesma sequência de valores? | Sim, com `--seed` |
| Posso reprocessar uma janela temporal? | Não |
| O sistema impede alerta duplicado? | Sim |
| O sistema impede leitura duplicada? | Não |

Esta é uma limitação documentada e aceita para o MVP. Idempotência formal
está no backlog como evolução futura.
