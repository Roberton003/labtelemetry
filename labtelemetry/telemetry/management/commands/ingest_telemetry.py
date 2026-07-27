import logging
import signal
from datetime import UTC, datetime

from django.core.management.base import BaseCommand

from telemetry.models import TelemetryReading, TelemetrySensor
from telemetry.quality import evaluate_reading, raise_alert

logger = logging.getLogger(__name__)

_shutdown_requested = False


def _handle_signal(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True


class Command(BaseCommand):
    help = "Ingest telemetry from external sources (Modbus TCP / Simulator)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", default="simulator", choices=["modbus", "opcua", "simulator"]
        )
        parser.add_argument(
            "--interval", type=float, default=5.0, help="Seconds between reads"
        )
        parser.add_argument(
            "--batch-size", type=int, default=10, help="Max samples per read"
        )

        # Modbus args
        parser.add_argument("--modbus-host", default="127.0.0.1")
        parser.add_argument("--modbus-port", type=int, default=502)
        parser.add_argument("--modbus-unit", type=int, default=1)
        parser.add_argument("--modbus-timeout", type=float, default=5.0)
        parser.add_argument(
            "--modbus-register",
            action="append",
            default=None,
            metavar="ADDRESS:SENSOR_ID[:SCALE]",
            help=(
                "Holding register e o sensor que ele alimenta, com escala "
                "opcional, ex.: '0:3:0.01' (registrador 0 -> sensor 3, valor "
                "= raw * 0.01). Repetivel, um por registrador."
            ),
        )

        # OPC-UA args
        parser.add_argument("--opcua-url", default="opc.tcp://localhost:4840")
        parser.add_argument("--opcua-timeout", type=float, default=5.0)
        parser.add_argument(
            "--opcua-node",
            action="append",
            default=None,
            metavar="NODE_ID:SENSOR_ID",
            help=(
                "Node OPC-UA e o sensor que ele alimenta, ex.: "
                "'ns=2;i=101:3'. Repetivel, um por node."
            ),
        )

        # Simulator args
        parser.add_argument("--sim-seed", type=int, default=42)
        parser.add_argument("--sim-count", type=int, default=10)
        parser.add_argument("--sim-anomaly-rate", type=float, default=0.0)

        # One-shot
        parser.add_argument("--once", action="store_true", help="Single read, no loop")

    def handle(self, *args, **options):
        global _shutdown_requested
        _shutdown_requested = False

        source = self._build_source(options)
        if source is None:
            self.stderr.write("Failed to create source")
            return

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        interval = options["interval"]
        batch_size = options["batch_size"]
        iteration = 0
        total_samples = 0
        total_processed = 0

        self.stdout.write(
            f"Source: {source.name}, interval={interval}s, batch_size={batch_size}"
        )

        try:
            while not _shutdown_requested:
                samples = source.read()
                if not samples:
                    self.stdout.write(f"[{iteration}] No samples from {source.name}")
                else:
                    batch: list[TelemetryReading] = []
                    for sample in samples[:batch_size]:
                        reading = self._sample_to_reading(sample)
                        if reading is not None:
                            # Avaliacao pura: nenhum acesso ao banco no loop.
                            reading.status = evaluate_reading(reading)
                            batch.append(reading)
                    if batch:
                        # ignore_conflicts + UniqueConstraint(sensor, timestamp):
                        # reprocessar a mesma janela e no-op, nao IntegrityError.
                        TelemetryReading.objects.bulk_create(
                            batch, ignore_conflicts=True
                        )
                        for reading in batch:
                            raise_alert(reading)
                        total_processed += len(batch)
                    total_samples += len(samples)
                    self.stdout.write(
                        f"[{iteration}] Read {len(samples)} samples, "
                        f"{total_processed} processed"
                    )

                iteration += 1
                if options["once"]:
                    break
                if not _shutdown_requested:
                    import time

                    time.sleep(interval)

            health = source.health()
        finally:
            source.close()

        self.stdout.write(
            f"Ingest complete: {total_samples} samples, {total_processed} processed. "
            f"Source health: {health.get('status', 'unknown')}"
        )

    def _build_source(self, options):
        source_type = options["source"]

        if source_type == "modbus":
            from telemetry.sources.modbus import ModbusTCPAdapter, RegisterSpec

            specs = options["modbus_register"]
            if not specs:
                self.stderr.write(
                    "--source modbus exige ao menos um --modbus-register "
                    "'ADDRESS:SENSOR_ID[:SCALE]' (ex.: '0:3:0.01')"
                )
                return None

            registers: list[RegisterSpec] = []
            for spec in specs:
                parsed = self._parse_register_spec(spec)
                if parsed is None:
                    return None
                registers.append(parsed)

            adapter = ModbusTCPAdapter(
                host=options["modbus_host"],
                port=options["modbus_port"],
                unit_id=options["modbus_unit"],
                timeout=options["modbus_timeout"],
                registers=registers,
            )
            adapter.connect()
            if not adapter._connected:
                self.stdout.write(
                    self.style.WARNING("Modbus not connected, use --source simulator")
                )
            return adapter

        if source_type == "opcua":
            from telemetry.sources.opcua import OpcUaAdapter

            specs = options["opcua_node"]
            if not specs:
                self.stderr.write(
                    "--source opcua exige ao menos um --opcua-node "
                    "'NODE_ID:SENSOR_ID' (ex.: 'ns=2;i=101:3')"
                )
                return None

            node_ids: list[str] = []
            sensor_ids: list[int] = []
            for spec in specs:
                # rsplit: node ids contem '=' e ';' (ns=2;i=101), mas o
                # sensor id fica sempre depois do ultimo ':'.
                node_id, _, raw_sensor_id = spec.rpartition(":")
                if not node_id or not raw_sensor_id.strip().isdigit():
                    self.stderr.write(
                        f"--opcua-node invalido: {spec!r}. "
                        "Formato esperado: 'NODE_ID:SENSOR_ID'."
                    )
                    return None
                node_ids.append(node_id)
                sensor_ids.append(int(raw_sensor_id))

            return OpcUaAdapter(
                url=options["opcua_url"],
                node_ids=node_ids,
                sensor_ids=sensor_ids,
                timeout=options["opcua_timeout"],
            )

        if source_type == "simulator":
            from telemetry.sources.simulator import SimulatorAdapter

            return SimulatorAdapter(
                seed=options["sim_seed"],
                count=options["sim_count"],
                anomaly_rate=options["sim_anomaly_rate"],
            )

        return None

    def _parse_register_spec(self, spec):
        """Converte 'ADDRESS:SENSOR_ID[:SCALE]' em RegisterSpec, ou None."""
        from telemetry.sources.modbus import RegisterSpec

        parts = spec.split(":")
        if len(parts) not in (2, 3):
            self.stderr.write(
                f"--modbus-register invalido: {spec!r}. "
                "Formato esperado: 'ADDRESS:SENSOR_ID[:SCALE]'."
            )
            return None

        address, sensor_id, scale = parts[0], parts[1], (parts[2] if len(parts) == 3 else "1")
        if not address.strip().isdigit() or not sensor_id.strip().isdigit():
            self.stderr.write(
                f"--modbus-register invalido: {spec!r}. "
                "ADDRESS e SENSOR_ID devem ser inteiros."
            )
            return None
        try:
            scale_value = float(scale)
        except ValueError:
            self.stderr.write(
                f"--modbus-register invalido: {spec!r}. SCALE deve ser numerico."
            )
            return None

        # O parametro vem do sensor no banco, nao do CLP: holding register nao
        # carrega unidade. Deixar vazio evita disparar o guard de divergencia
        # em _sample_to_reading com uma comparacao sem sentido.
        return RegisterSpec(
            address=int(address), sensor_id=int(sensor_id), scale=scale_value
        )

    def _sample_to_reading(self, sample):
        try:
            sensor = TelemetrySensor.objects.get(id=sample.sensor_id)
        except TelemetrySensor.DoesNotExist:
            logger.warning("Sensor %d not found, skipping", sample.sensor_id)
            return None

        # Mapeamento errado (node/registrador apontando para o sensor errado)
        # produz dado plausivel e silenciosamente incorreto. Avisa sem
        # descartar: o browse name da fonte pode legitimamente divergir.
        if sample.parameter and sample.parameter != sensor.parameter:
            logger.warning(
                "Sensor %d e %s, mas a fonte enviou %s — verifique o mapeamento",
                sensor.id,
                sensor.parameter,
                sample.parameter,
            )

        timestamp = sample.timestamp or datetime.now(UTC)

        raw_val = round(sample.value, 4)
        calibrated_val = round(raw_val * sensor.calibration_factor, 4)

        return TelemetryReading(
            sensor=sensor,
            timestamp=timestamp,
            raw_value=raw_val,
            calibrated_value=calibrated_val,
            source=sample.source[:100],
        )
