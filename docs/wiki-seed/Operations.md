[[Home]] | [[Overview]] | [[Architecture]] | [[Idempotencia-e-Replay]] | [[API]] | [[Operations]] | [[Validation-Guide]]

# 🚀 Operações

---

## 📦 Setup Local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
docker compose up -d
.venv/bin/python labtelemetry/manage.py migrate
```

**Nota sobre o banco:** sem `DATABASE_URL` definida, o projeto cai em SQLite — útil para inspeção rápida, mas o CI e o Compose rodam em PostgreSQL 16. Para apontar ao Postgres local:

```bash
export DATABASE_URL="postgres://labtelemetry:labtelemetry_dev@localhost:5432/labtelemetry"
```

---

## ▶️ Executar a Aplicação

```bash
.venv/bin/python labtelemetry/manage.py runserver 127.0.0.1:8000
```

| Serviço | Endereço |
|---|---|
| Dashboard | http://127.0.0.1:8000/ |
| Admin | http://127.0.0.1:8000/admin/ |
| Jaeger | http://127.0.0.1:16686 |

---

## 📡 Gerar Telemetria

**Simulador (reproduzível):**

```bash
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --once --sim-count 3
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source simulator --interval 5
```

**Modbus TCP (fonte real):**

```bash
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source modbus \
  --modbus-host 192.168.0.10 --modbus-port 502 --modbus-unit 1 \
  --modbus-register "0:1:0.01" \
  --modbus-register "4:2:0.1"
```

**Formato do `--modbus-register`:** `ADDRESS:SENSOR_ID[:SCALE]`, repetível, um por registrador. A escala existe porque holding register é uint16 — o CLP publica `740` e o pH real é `7.40`. Omitida, vale `1.0`. Sem ao menos um mapeamento o comando recusa iniciar.

**OPC-UA (fonte real):**

```bash
.venv/bin/python labtelemetry/manage.py ingest_telemetry --source opcua \
  --opcua-url opc.tcp://plc.local:4840 \
  --opcua-node "ns=2;i=101:1" \
  --opcua-node "ns=2;i=103:5"
```

**Formato do `--opcua-node`:** `NODE_ID:SENSOR_ID`, repetível, um por node. O split acontece no **último** `:` — node ids contêm `=` e `;` (`ns=2;i=101`), então isso não colide. Sem ao menos um mapeamento, o comando recusa iniciar: índice posicional de node não é chave primária de sensor.

**Cenário sintético com anomalias:**

```bash
.venv/bin/python labtelemetry/manage.py simulate_telemetry --seed 42 --iterations 50 --anomaly-rate 0.3
```

**Diferença entre os dois comandos:** `ingest_telemetry` é o runner de produção — lê de uma fonte real via adapter. `simulate_telemetry` gera cenário direto no banco, para exercitar as regras de qualidade sem depender de fonte externa.

**Sobre reexecução:** rodar `ingest_telemetry` duas vezes sobre a mesma janela é no-op; rodar `simulate_telemetry` duas vezes gera linhas novas. O porquê está em [[Idempotencia-e-Replay]].

---

## 🖥️ O Que a Interface Mostra

- cards de resumo
- saúde das fontes
- leituras recentes
- alertas ativos
- lista de sensores

Todos atualizados por HTMX em fragmentos parciais independentes.

---

## ✅ Checagens de Sanidade

```bash
.venv/bin/python labtelemetry/manage.py check
.venv/bin/python labtelemetry/manage.py makemigrations --check --dry-run
.venv/bin/python labtelemetry/manage.py test telemetry
.venv/bin/ruff check labtelemetry/
```

As mesmas quatro checagens rodam no CI a cada push e pull request. Para o fluxo completo em terminais paralelos, ver [[Validation-Guide]].
