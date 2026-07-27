from datetime import UTC, datetime
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, tag

from telemetry.models import TelemetryAlert, TelemetryReading, TelemetrySensor
from telemetry.sources.base import TelemetrySample


class _StubSource:
    def __init__(self, name, samples, health=None):
        self._name = name
        self._samples = list(samples)
        self._health = health or {"name": name, "status": "ok", "last_read": None}
        self.closed = False

    @property
    def name(self):
        return self._name

    def read(self):
        return list(self._samples)

    def health(self):
        return dict(self._health)

    def close(self):
        self.closed = True


class _FakeModbusAdapter:
    instances = []

    # Valor bruto que o "CLP" publica em cada holding register (uint16).
    RAW_BY_ADDRESS = {0: 740, 4: 210}

    def __init__(
        self, host="127.0.0.1", port=502, unit_id=1, timeout=5.0, client=None,
        registers=None,
    ):
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._timeout = timeout
        self._client = client
        self._connected = False
        self.closed = False
        self._last_read = None
        self._registers = registers
        _FakeModbusAdapter.instances.append(self)

    @property
    def name(self):
        return f"modbus:{self._host}:{self._port}"

    def connect(self):
        self._connected = True

    def read(self):
        if not self._connected:
            return []
        self._last_read = datetime.now(UTC)
        # Reproduz o contrato do adapter real: valor = raw * scale.
        return [
            TelemetrySample(
                sensor_id=spec.sensor_id,
                parameter=spec.parameter,
                value=self.RAW_BY_ADDRESS[spec.address] * spec.scale,
                timestamp=self._last_read,
                source=self.name,
                raw_payload={
                    "register": spec.address,
                    "raw": self.RAW_BY_ADDRESS[spec.address],
                    "scale": spec.scale,
                },
            )
            for spec in (self._registers or [])
        ]

    def health(self):
        return {
            "name": self.name,
            "status": "connected" if self._connected else "disconnected",
            "last_read": self._last_read.isoformat() if self._last_read else None,
            "host": self._host,
            "port": self._port,
        }

    def close(self):
        self.closed = True
        self._connected = False


class IngestTelemetryCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sensor_ph = TelemetrySensor.objects.create(id=1, name="Sensor pH", parameter="PH")
        cls.sensor_turb = TelemetrySensor.objects.create(id=2, name="Sensor Turbidez", parameter="TURBIDITY")

    def test_once_with_stub_source_persists_readings_and_alerts(self):
        source = _StubSource(
            "stub:simulator",
            [
                TelemetrySample(
                    sensor_id=self.sensor_ph.id,
                    parameter=self.sensor_ph.parameter,
                    value=7.0,
                    timestamp=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
                    source="stub:simulator",
                    raw_payload={"value": 7.0},
                ),
                TelemetrySample(
                    sensor_id=self.sensor_turb.id,
                    parameter=self.sensor_turb.parameter,
                    value=6.5,
                    timestamp=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
                    source="stub:simulator",
                    raw_payload={"value": 6.5},
                ),
            ],
            health={"name": "stub:simulator", "status": "ok", "last_read": "2026-06-23T12:00:00+00:00"},
        )

        out = StringIO()
        with mock.patch("telemetry.management.commands.ingest_telemetry.Command._build_source", return_value=source):
            call_command("ingest_telemetry", "--source", "simulator", "--once", stdout=out)

        self.assertTrue(source.closed)
        self.assertEqual(TelemetryReading.objects.count(), 2)
        self.assertEqual(TelemetryAlert.objects.count(), 1)
        reading = TelemetryReading.objects.get(sensor=self.sensor_turb)
        self.assertEqual(reading.status, "OUT_OF_BOUNDS")
        self.assertEqual(reading.source, "stub:simulator")
        self.assertIn("Source health: ok", out.getvalue())

    def test_replay_same_window_is_idempotent(self):
        """Reprocessar a mesma janela nao duplica nem levanta IntegrityError.

        Teste negativo do guardrail: a garantia vem da
        UniqueConstraint(sensor, timestamp) combinada com
        bulk_create(ignore_conflicts=True). Antes desse par, a segunda
        execucao estourava IntegrityError e derrubava o loop de ingestao.
        """
        ts = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
        samples = [
            TelemetrySample(
                sensor_id=self.sensor_ph.id,
                parameter=self.sensor_ph.parameter,
                value=7.0,
                timestamp=ts,
                source="stub:replay",
            ),
            TelemetrySample(
                sensor_id=self.sensor_turb.id,
                parameter=self.sensor_turb.parameter,
                value=6.5,
                timestamp=ts,
                source="stub:replay",
            ),
        ]

        for _ in range(2):
            source = _StubSource("stub:replay", samples)
            with mock.patch(
                "telemetry.management.commands.ingest_telemetry.Command._build_source",
                return_value=source,
            ):
                call_command(
                    "ingest_telemetry", "--source", "simulator", "--once",
                    stdout=StringIO(),
                )

        self.assertEqual(TelemetryReading.objects.count(), 2)
        # raise_alert tambem e idempotente: o alerta de turbidez nao duplica.
        self.assertEqual(TelemetryAlert.objects.count(), 1)

    def test_once_with_modbus_source_uses_adapter_configuration(self):
        out = StringIO()
        with mock.patch("telemetry.sources.modbus.ModbusTCPAdapter", _FakeModbusAdapter):
            call_command(
                "ingest_telemetry",
                "--source",
                "modbus",
                "--once",
                "--modbus-host",
                "plc.local",
                "--modbus-port",
                "1502",
                "--modbus-unit",
                "7",
                "--modbus-timeout",
                "0.25",
                # register 0 -> sensor pH, raw 740 com escala 0.01 => 7.40
                "--modbus-register",
                f"0:{self.sensor_ph.id}:0.01",
                stdout=out,
            )

        self.assertGreaterEqual(len(_FakeModbusAdapter.instances), 1)
        adapter = _FakeModbusAdapter.instances[-1]
        self.assertEqual(adapter._host, "plc.local")
        self.assertEqual(adapter._port, 1502)
        self.assertEqual(adapter._unit_id, 7)
        self.assertAlmostEqual(adapter._timeout, 0.25)
        self.assertTrue(adapter.closed)
        self.assertEqual(TelemetryReading.objects.count(), 1)
        reading = TelemetryReading.objects.get(sensor=self.sensor_ph)
        # Sem a escala, o uint16 740 entraria como pH 740 e cairia em
        # OUT_OF_BOUNDS. Com ela, 7.40 e um pH plausivel.
        self.assertAlmostEqual(reading.raw_value, 7.40, places=2)
        self.assertEqual(reading.status, "NORMAL")
        self.assertEqual(reading.source, "modbus:plc.local:1502")
        self.assertIn("Source health: connected", out.getvalue())

    def test_modbus_requires_register_mapping(self):
        with mock.patch("telemetry.sources.modbus.ModbusTCPAdapter", _FakeModbusAdapter):
            err = StringIO()
            call_command(
                "ingest_telemetry", "--source", "modbus", "--once",
                stdout=StringIO(), stderr=err,
            )

        self.assertIn("--modbus-register", err.getvalue())
        self.assertEqual(TelemetryReading.objects.count(), 0)


class ModbusRegisterSpecParsingTest(TestCase):
    def _parse(self, spec):
        from telemetry.management.commands.ingest_telemetry import Command

        cmd = Command()
        cmd.stderr = StringIO()
        return cmd._parse_register_spec(spec), cmd.stderr.getvalue()

    def test_scale_defaults_to_one_when_omitted(self):
        parsed, _ = self._parse("4:12")
        self.assertEqual((parsed.address, parsed.sensor_id, parsed.scale), (4, 12, 1.0))

    def test_scale_is_parsed_when_present(self):
        parsed, _ = self._parse("0:3:0.01")
        self.assertEqual((parsed.address, parsed.sensor_id), (0, 3))
        self.assertAlmostEqual(parsed.scale, 0.01)

    def test_rejects_non_numeric_fields(self):
        for bad in ("a:3", "0:b", "0:3:xyz", "0", "0:3:1:9"):
            with self.subTest(spec=bad):
                parsed, err = self._parse(bad)
                self.assertIsNone(parsed, f"{bad!r} deveria ser rejeitado")
                self.assertIn("invalido", err)


class ModbusAdapterScalingTest(TestCase):
    class _FakeClient:
        """Cliente pymodbus minimo: devolve o raw configurado por endereco."""

        def __init__(self, raw_by_address):
            self._raw = raw_by_address
            self.addresses_read = []

        def read_holding_registers(self, address, count, slave):
            self.addresses_read.append(address)
            return mock.Mock(
                isError=lambda: False, registers=[self._raw[address]]
            )

        def connect(self):
            return True

        def close(self):
            pass

    def test_reads_only_configured_registers_and_applies_scale(self):
        from telemetry.sources.modbus import ModbusTCPAdapter, RegisterSpec

        client = self._FakeClient({0: 723, 7: 45})
        adapter = ModbusTCPAdapter(
            client=client,
            registers=[
                RegisterSpec(address=0, sensor_id=3, scale=0.01),
                RegisterSpec(address=7, sensor_id=9, scale=0.1),
            ],
        )
        adapter.connect()

        samples = adapter.read()

        # Le so os enderecos configurados — nao um bloco 0..N.
        self.assertEqual(client.addresses_read, [0, 7])
        self.assertEqual([s.sensor_id for s in samples], [3, 9])
        self.assertAlmostEqual(samples[0].value, 7.23)
        self.assertAlmostEqual(samples[1].value, 4.5)
        self.assertEqual(samples[0].raw_payload["raw"], 723)
        self.assertAlmostEqual(samples[0].raw_payload["scale"], 0.01)

    def test_failed_register_is_skipped_without_losing_the_others(self):
        from telemetry.sources.modbus import ModbusTCPAdapter, RegisterSpec

        class _PartiallyFailingClient(self.__class__._FakeClient):
            def read_holding_registers(self, address, count, slave):
                if address == 0:
                    return mock.Mock(isError=lambda: True)
                return super().read_holding_registers(address, count, slave)

        adapter = ModbusTCPAdapter(
            client=_PartiallyFailingClient({0: 1, 7: 45}),
            registers=[
                RegisterSpec(address=0, sensor_id=3, scale=0.01),
                RegisterSpec(address=7, sensor_id=9, scale=0.1),
            ],
        )
        adapter.connect()

        samples = adapter.read()

        self.assertEqual([s.sensor_id for s in samples], [9])


class IngestOpcUaSourceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sensor_ph = TelemetrySensor.objects.create(
            id=11, name="pH Reator", parameter="PH"
        )
        cls.sensor_toc = TelemetrySensor.objects.create(
            id=12, name="TOC Saida", parameter="TOC"
        )

    def _build(self, argv):
        """Roda _build_source com argv e devolve o adapter (ou None)."""
        from telemetry.management.commands.ingest_telemetry import Command

        cmd = Command()
        parser = cmd.create_parser("manage.py", "ingest_telemetry")
        options = vars(parser.parse_args(argv))
        cmd.stderr = StringIO()
        return cmd._build_source(options), cmd.stderr.getvalue()

    def test_node_spec_maps_each_node_to_its_sensor(self):
        adapter, _ = self._build([
            "--source", "opcua",
            "--opcua-url", "opc.tcp://plc.local:4840",
            "--opcua-node", "ns=2;i=101:11",
            "--opcua-node", "ns=2;i=103:12",
        ])

        self.assertIsNotNone(adapter)
        # Node ids carregam '=' e ';' — o split e no ultimo ':', nao no primeiro.
        self.assertEqual(adapter._node_ids, ["ns=2;i=101", "ns=2;i=103"])
        self.assertEqual(adapter._sensor_ids, [11, 12])
        self.assertEqual(adapter.name, "opcua:opc.tcp://plc.local:4840")

    def test_missing_node_mapping_is_rejected(self):
        adapter, err = self._build(["--source", "opcua"])
        self.assertIsNone(adapter)
        self.assertIn("--opcua-node", err)

    def test_malformed_node_spec_is_rejected(self):
        adapter, err = self._build([
            "--source", "opcua", "--opcua-node", "ns=2;i=101",
        ])
        self.assertIsNone(adapter)
        self.assertIn("invalido", err)

    def test_sensor_ids_must_match_node_count(self):
        from telemetry.sources.opcua import OpcUaAdapter

        with self.assertRaises(ValueError):
            OpcUaAdapter(node_ids=["ns=2;i=101", "ns=2;i=102"], sensor_ids=[11])

    def test_parameter_mismatch_warns_but_still_ingests(self):
        """Node apontado para o sensor errado avisa, sem descartar o dado."""
        source = _StubSource(
            "stub:opcua",
            [
                TelemetrySample(
                    sensor_id=self.sensor_ph.id,   # sensor e PH
                    parameter="TOC",               # mas a fonte diz TOC
                    value=7.0,
                    timestamp=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
                    source="stub:opcua",
                ),
            ],
        )

        with mock.patch(
            "telemetry.management.commands.ingest_telemetry.Command._build_source",
            return_value=source,
        ):
            with self.assertLogs(
                "telemetry.management.commands.ingest_telemetry", level="WARNING"
            ) as logs:
                call_command("ingest_telemetry", "--once", stdout=StringIO())

        self.assertTrue(
            any("verifique o mapeamento" in m for m in logs.output),
            f"esperava aviso de mapeamento, obtive: {logs.output}",
        )
        self.assertEqual(TelemetryReading.objects.count(), 1)

    @tag("integration")
    def test_end_to_end_against_live_opcua_server_persists_readings(self):
        """Integracao: servidor OPC-UA real -> comando -> leituras no banco."""
        import time

        from telemetry.sources.opcua_test_server import (
            DEFAULT_PORT,
            PH_NODE_ID,
            TOC_NODE_ID,
            run_test_server,
        )

        port = DEFAULT_PORT + 1
        thread = run_test_server(port)
        try:
            out = StringIO()
            # O servidor pode demorar a ficar pronto; o comando so persiste
            # quando ha amostras, entao tentamos ate 3x.
            for _ in range(3):
                call_command(
                    "ingest_telemetry",
                    "--source", "opcua",
                    "--once",
                    "--opcua-url", f"opc.tcp://127.0.0.1:{port}",
                    "--opcua-timeout", "5",
                    "--opcua-node", f"{PH_NODE_ID}:{self.sensor_ph.id}",
                    "--opcua-node", f"{TOC_NODE_ID}:{self.sensor_toc.id}",
                    stdout=out,
                )
                if TelemetryReading.objects.exists():
                    break
                time.sleep(1)

            readings = {r.sensor_id: r for r in TelemetryReading.objects.all()}
            self.assertEqual(set(readings), {self.sensor_ph.id, self.sensor_toc.id})
            # Valores do servidor de teste: PH=7.0, TOC=5.0
            self.assertAlmostEqual(readings[self.sensor_ph.id].raw_value, 7.0, delta=0.1)
            self.assertAlmostEqual(readings[self.sensor_toc.id].raw_value, 5.0, delta=0.1)
            self.assertIn("opcua:", readings[self.sensor_ph.id].source)
            # PH=7.0 esta dentro de 6.0-8.5 e TOC=5.0 abaixo de 10.0
            self.assertEqual(readings[self.sensor_ph.id].status, "NORMAL")
            self.assertEqual(readings[self.sensor_toc.id].status, "NORMAL")
        finally:
            thread.join(timeout=2)


class SourceHealthEndpointTest(TestCase):
    def test_returns_status_for_all_three_sources(self):
        resp = self.client.get("/api/health/sources/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("simulator", data)
        self.assertIn("modbus", data)
        self.assertIn("opcua", data)
        self.assertEqual(data["simulator"]["name"], "simulator:seed=42")
        self.assertEqual(data["simulator"]["status"], "ok")
        self.assertIn(data["modbus"]["status"], {"disconnected", "unavailable"})
        self.assertIn(data["opcua"]["status"], {"unknown", "unavailable"})
