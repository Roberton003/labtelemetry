"""OPC-UA test server for integration tests.

Provides a simple thread-based server that exposes PH, TURBIDITY, and TOC
variables via OPC-UA on localhost.
"""

import asyncio
import logging
import socket
import threading
import time

logger = logging.getLogger(__name__)

DEFAULT_PORT = 14840
PH_NODE_ID = "ns=2;i=101"
TURBIDITY_NODE_ID = "ns=2;i=102"
TOC_NODE_ID = "ns=2;i=103"
ALL_NODE_IDS = [PH_NODE_ID, TURBIDITY_NODE_ID, TOC_NODE_ID]


def _wait_for_server(port: int, timeout: float = 5.0) -> bool:
    """Actively poll until the OPC-UA server is reachable on *port*.

    Duas fases de proposito: um handshake OPC-UA completo arrasta todo o stack
    asyncua e, sob `coverage run`, cada tentativa e tracada linha a linha —
    poll a 100ms nesse formato consome o timeout inteiro sem chegar a
    conectar. A fase 1 usa socket cru (barato de tracar) para esperar a porta
    abrir; so entao a fase 2 confirma que o endpoint OPC-UA responde.
    """
    from asyncua import Client

    deadline = time.monotonic() + timeout

    # Fase 1: a porta esta escutando?
    listening = False
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                listening = True
                break
        time.sleep(0.05)

    if not listening:
        return False

    # Fase 2: o endpoint OPC-UA ja aceita sessao? (aceitar TCP nao basta)
    async def _probe() -> None:
        # connect e disconnect PRECISAM do mesmo event loop: a conexao fica
        # atrelada ao loop onde foi aberta. Dois `asyncio.run()` separados
        # abrem a sessao num loop e tentam fecha-la em outro, o que sempre
        # levanta excecao — o probe nunca retornava sucesso.
        async with Client(f"opc.tcp://127.0.0.1:{port}"):
            pass

    while time.monotonic() < deadline:
        try:
            asyncio.run(_probe())
            return True
        except Exception:
            time.sleep(0.2)
    return False


def run_test_server(
    port: int = DEFAULT_PORT, startup_timeout: float = 20.0
) -> threading.Thread:
    """Start an OPC-UA test server in a daemon thread. Returns the thread.

    The server exposes PH (7.0), TURBIDITY (2.0), and TOC (5.0) variables
    under namespace 'http://labtelemetry.test.opcua'.

    Blocks until the server is reachable or *startup_timeout* elapses. O
    startup local fica em ~2s; o teto de 20s e margem para um runner de CI
    carregado. O caminho feliz retorna assim que o servidor responde, entao o
    teto alto nao custa nada quando as coisas vao bem.
    """
    thread = threading.Thread(
        target=_start_server,
        args=(port,),
        daemon=True,
        name="opcua-test-server",
    )
    thread.start()
    if not _wait_for_server(port, timeout=startup_timeout):
        logger.warning(
            "OPC-UA test server did not become reachable within %ss", startup_timeout
        )
    return thread


async def _async_server(port: int) -> None:
    """Start the OPC-UA server (async body)."""
    from asyncua import Server

    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://127.0.0.1:{port}")

    uri = "http://labtelemetry.test.opcua"
    idx = await server.register_namespace(uri)

    objects = server.nodes.objects
    obj = await objects.add_object(idx, "Sensors")

    from asyncua import ua

    ph = await obj.add_variable(
        ua.NodeId(101, idx),
        "PH",
        7.0,
    )
    await ph.set_writable(True)

    turb = await obj.add_variable(
        ua.NodeId(102, idx),
        "TURBIDITY",
        2.0,
    )
    await turb.set_writable(True)

    toc = await obj.add_variable(
        ua.NodeId(103, idx),
        "TOC",
        5.0,
    )
    await toc.set_writable(True)

    async with server:
        await asyncio.Event().wait()  # run forever


def _start_server(port: int) -> None:
    """Thread target: run the OPC-UA server.

    Nao rode sob `coverage run`: com o tracer ativo o startup passa de ~2s
    para ~56s (medido), porque o event loop do asyncua e tracado linha a
    linha. Os testes que dependem deste servidor sao marcados
    `@tag("integration")` e ficam fora do passo de cobertura no CI.
    """
    asyncio.run(_async_server(port))
