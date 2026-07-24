[[Home]] | [[Overview]] | [[Architecture]] | [[Idempotencia-e-Replay]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# 🔁 Idempotência e Replay

Reprocessar dados é rotina em pipeline operacional — o CLP reconecta, o job reinicia, alguém roda o comando duas vezes. Esta página descreve exatamente o que acontece nesses casos.

---

## 🔒 A Garantia

**Mecanismo:** `UniqueConstraint(fields=["sensor", "timestamp"])` no modelo, combinada com `bulk_create(batch, ignore_conflicts=True)` na ingestão.

**Efeito:** reprocessar a mesma janela `(sensor, timestamp)` é no-op. As linhas já existentes são descartadas pelo banco — sem erro, sem duplicata.

**Por que no banco e não na aplicação:** a alternativa natural seria `get_or_create()` por amostra, o que adiciona um `SELECT` por leitura antes de cada `INSERT`. A constraint move a checagem para dentro do Postgres e para o nível do lote — um round-trip por ciclo de leitura em vez de N.

**Trade-off aceito:** `ignore_conflicts=True` não devolve chaves primárias confiáveis. O comando de ingestão por isso reporta amostras processadas, não linhas criadas — um contador honesto em vez de um número bonito.

---

## 🧪 O Teste Negativo

**Princípio:** um guardrail só existe depois que alguém tentou violá-lo e observou o bloqueio. Configuração declarativa não prova comportamento.

**Teste:** `telemetry.test_ingest_telemetry.IngestTelemetryCommandTest.test_replay_same_window_is_idempotent`

**Método:** executa a mesma janela de leituras duas vezes e afirma que a contagem não dobra.

**Verificação:** removendo o mecanismo, o teste falha com `IntegrityError: UNIQUE constraint failed: telemetry_telemetryreading.sensor_id, telemetry_telemetryreading.timestamp` — comportamento observado, não presumido.

---

## ⚠️ O Que NÃO É Garantido

A identidade de uma leitura é o par `(sensor, timestamp)`, e nada além disso. Duas consequências diretas:

- **Colisão de valor:** dois valores diferentes no mesmo `(sensor, timestamp)` colapsam no primeiro. A segunda leitura é descartada, não corrigida — não há upsert, não há "última escrita vence".
- **Timestamp novo nunca deduplica:** se a fonte carimba `timestamp = agora`, cada execução é uma janela nova e insere linhas novas. Isso é correto: são observações distintas.

**Consequência prática:** `simulate_telemetry --seed 42` executado duas vezes produz 20 linhas, não 10. O seed garante **repetibilidade do valor**, não idempotência de inserção — são propriedades diferentes, e confundi-las é a origem mais comum de expectativa frustrada em replay.

---

## 🗺️ Mapa de Idempotência

| Componente | Idempotente? | Mecanismo |
|---|---|---|
| `ingest_telemetry` — mesmo sensor+timestamp | ✅ Sim | Constraint + `ignore_conflicts` |
| `ingest_telemetry` — timestamp novo | ❌ Não | Janela diferente = leitura diferente, por definição |
| `quality.raise_alert()` | ✅ Sim | Não recria alerta se já houver um ativo do mesmo tipo |
| `GET /api/...` | ✅ Sim | Contrato HTTP |
| `migrate` | ✅ Sim | Migrations do Django |
| `simulate_telemetry` | ❌ Não | Carimba `timestamp = agora` |

---

## 🚧 Caminho para Exactly-Once Formal

Fora do escopo atual, registrado como evolução consciente:

- **Chave natural mais forte:** incluir `source` na constraint, para que simulador e Modbus não disputem o mesmo `(sensor, timestamp)`.
- **Upsert real:** `bulk_create(update_conflicts=True)` — a releitura corrige o valor em vez de descartá-lo.
- **Hash de payload** como identidade do evento, desacoplando a deduplicação da precisão do timestamp.
- **Janela de replay explícita:** `--start-time` / `--end-time` no comando de ingestão.

Detalhamento em [docs/replay-idempotency.md](https://github.com/Roberton003/labtelemetry/blob/master/docs/replay-idempotency.md) no repositório.
