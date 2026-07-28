# Replay, Deduplicação e Idempotência

## Contexto

O LabTelemetry não oferece garantia formal de *exactly-once*. Este documento
descreve o comportamento real do sistema — o que é garantido, o que não é, e
onde exatamente fica a fronteira — para que ninguém descubra o limite em
produção.

## A garantia que existe

A deduplicação é feita **no banco, não na aplicação**:

```python
# telemetry/models.py
class Meta:
    constraints = [
        UniqueConstraint(fields=["sensor", "timestamp"], name="uq_sensor_timestamp"),
    ]
```

```python
# telemetry/management/commands/ingest_telemetry.py
TelemetryReading.objects.bulk_create(batch, ignore_conflicts=True)
```

O par constraint + `ignore_conflicts` é o que dá a garantia. Reprocessar a
mesma janela `(sensor, timestamp)` é **no-op**: as linhas já existentes são
descartadas pelo banco, sem erro e sem duplicata.

Optar pela constraint em vez de um `get_or_create` por leitura é deliberado:
a checagem acontece uma vez por lote, dentro do banco, em vez de um `SELECT`
por amostra vindo da aplicação.

### Teste negativo

A garantia não é uma alegação deste documento — ela tem um teste que falha
quando o mecanismo é removido:

```
telemetry.test_ingest_telemetry.IngestTelemetryCommandTest
    .test_replay_same_window_is_idempotent
```

Ele executa a mesma janela duas vezes e afirma que a contagem de leituras não
dobra. Sem `ignore_conflicts`, a segunda execução levanta
`IntegrityError: UNIQUE constraint failed` e derruba o loop de ingestão —
comportamento verificado antes do fix, não presumido.

## A garantia que NÃO existe

`(sensor, timestamp)` é a chave de deduplicação. Isso tem duas consequências
que valem estar explícitas:

1. **Dois valores diferentes no mesmo `(sensor, timestamp)` colapsam no
   primeiro.** A segunda leitura é silenciosamente descartada, não corrigida.
   Não há *upsert*, não há "última escrita vence".
2. **Timestamps diferentes nunca deduplicam**, mesmo com valor idêntico. Se a
   fonte carimba `timestamp = agora`, cada execução é uma janela nova — e
   portanto insere linhas novas, corretamente.

Não há hash de payload nem identificador de evento da fonte externa. A
identidade de uma leitura é o par sensor/instante, e nada além disso.

## Como replay funciona na prática

### Reproduzir uma sequência de valores

```bash
simulate_telemetry --seed 42 --iterations 10 --anomaly-rate 0.3
```

O `--seed` garante **repetibilidade do valor**, não idempotência de inserção —
são coisas distintas. Como `simulate_telemetry` carimba `timestamp = agora` a
cada execução, rodar duas vezes produz 20 linhas com os mesmos 10 valores em
instantes diferentes. Isso é o comportamento correto: são duas observações
distintas do mesmo cenário simulado.

### Reprocessar uma janela vinda de uma fonte OT

Quando a fonte fornece o timestamp (Modbus e OPC-UA fornecem), o replay é
idempotente de verdade:

```bash
# Executar duas vezes sobre a mesma janela da fonte
python manage.py ingest_telemetry --source modbus --once --modbus-register "0:1:0.01"
python manage.py ingest_telemetry --source modbus --once --modbus-register "0:1:0.01"
# As leituras cujo (sensor, timestamp) ja existe sao descartadas pelo banco
```

Não há, hoje, um `--start-time`/`--end-time` para pedir uma janela histórica
explícita à fonte. Replay dirigido por janela está fora do escopo atual.

## Mapa de idempotência

| Componente | Idempotente? | Mecanismo |
|---|---|---|
| `ingest_telemetry` (mesmo sensor+timestamp) | ✅ Sim | `UniqueConstraint` + `bulk_create(ignore_conflicts=True)` |
| `ingest_telemetry` (timestamp novo a cada leitura) | ❌ Não | Janela diferente = leitura diferente, por definição |
| `quality.raise_alert()` | ✅ Sim | Não recria alerta se já houver um ativo do mesmo tipo para o sensor |
| `GET /api/...` | ✅ Sim | GET é idempotente por contrato HTTP |
| `migrate` | ✅ Sim | Migrations do Django |
| `simulate_telemetry` | ❌ Não | Carimba `timestamp = agora`; cada execução é uma janela nova |

## O que mudaria para exactly-once formal

Fora do escopo atual, registrado como evolução:

1. **Chave natural mais forte:** incluir `source` na constraint, para que
   simulador e Modbus não disputem o mesmo `(sensor, timestamp)`.
2. **Upsert de verdade:** `INSERT ... ON CONFLICT DO UPDATE` via
   `bulk_create(update_conflicts=True)`, para que a releitura corrija o valor
   em vez de descartá-lo.
3. **Hash de payload** como identidade do evento, desacoplando a deduplicação
   da precisão do timestamp.
4. **Janela de replay explícita:** `--start-time` / `--end-time` no comando de
   ingestão.

## Resumo

| Pergunta | Resposta |
|---|---|
| Posso reexecutar a ingestão da mesma janela? | Sim — é no-op, não duplica nem falha |
| Posso reproduzir a mesma sequência de valores? | Sim, com `--seed` |
| Uma releitura corrige um valor já gravado? | Não — é descartada |
| Posso pedir uma janela histórica à fonte? | Não |
| O sistema impede alerta duplicado? | Sim |
