[[Home]] | [[Overview]] | [[Architecture]] | [[Idempotencia-e-Replay]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# 🔗 API

Todos os endpoints JSON são servidos sob `/api/`. São somente leitura — a escrita acontece pelos comandos de ingestão.

---

## 📍 Endpoints

| Método | Rota | Função |
|---|---|---|
| GET | `/api/summary/` | Resumo operacional: contagens e última leitura |
| GET | `/api/sensors/` | Inventário de sensores |
| GET | `/api/readings/recent/?limit=50` | Leituras recentes (teto de 500) |
| GET | `/api/sensors/<id>/readings/?limit=100` | Série temporal de um sensor (teto de 500) |
| GET | `/api/alerts/active/` | Alertas ativos |
| GET | `/api/health/sources/` | Estado de conexão de cada fonte OT |

---

## 📦 Formato do Payload

**Leitura:** `sensor_name`, `parameter`, `timestamp`, `raw_value`, `calibrated_value`, `source`, `status`.

**Por que bruto e calibrado juntos:** o valor calibrado é o que o processo enxerga; o bruto é o que o sensor mandou. A divergência entre os dois é o que a detecção de drift observa — descartar o bruto tornaria a regra inauditável depois do fato.

**Campo `source`:** lineage curto (`simulator:seed=42`, `modbus:host:port`), suficiente para rastrear a origem em consulta sem carregar o payload do protocolo.

---

## 🚦 Exemplo

```bash
curl -s http://127.0.0.1:8000/api/summary/
# {"total_sensors": 6, "total_readings": 10, "active_alerts": 0,
#  "last_reading_timestamp": "2026-07-24T23:07:23.761Z"}

curl -s http://127.0.0.1:8000/api/health/sources/
# {"simulator": {"name": "simulator:seed=42", "status": "ok", ...},
#  "modbus": {"name": "modbus:127.0.0.1:502", "status": "disconnected", ...}}
```

---

## ⚠️ Fora do Contrato

- **Rotas antigas sem o prefixo `/api/`** não fazem parte do contrato público.
- **`/api/health/sources/` é metadado operacional**, não teste de conectividade ao vivo — reporta o último estado conhecido do adapter, não abre uma conexão Modbus a cada request.
- **Não há SLO público de latência.**

Contrato formal e regras de versionamento em [docs/data-contract.md](https://github.com/Roberton003/labtelemetry/blob/master/docs/data-contract.md).
