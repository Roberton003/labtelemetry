"""OPC-UA test server for integration tests.

Provides a simple thread-based server that exposes PH, TURBIDITY, and TOC
variables via OPC-UA on localhost.
"""

import asyncio
import logging
import threading
import time

logger = logging.getLogger(__name__)

DEFAULT_PORT = 14840
PH_NODE_ID = "ns=2;i=101"
TURBIDITY_NODE_ID = "ns=2;i=102"
TOC_NODE_ID = "ns=2;i=103"
ALL_NODE_IDS = [PH_NODE_ID, TURBIDITY_NODE_ID, TOC_NODE_ID]


def _wait_for_server(port: int, timeout: float = 5.0) -> bool:
    """Actively poll until the OPC-UA server is reachable on *port*."""
    from asyncua import Client

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            c = Client(f"opc.tcp://127.0.0.1:{port}")
            asyncio.run(c.connect())
            asyncio.run(c.disconnect())
            return True
        except ConnectionRefusedError:
            time.sleep(0.1)
        except Exception:
            time.sleep(0.1)
    return False


def run_test_server(port: int = DEFAULT_PORT) -> threading.Thread:
    """Start an OPC-UA test server in a daemon thread. Returns the thread.

    The server exposes PH (7.0), TURBIDITY (2.0), and TOC (5.0) variables
    under namespace 'http://labtelemetry.test.opcua'.

    Blocks until the server is reachable or a 10-second timeout elapses.
    """
    thread = threading.Thread(
        target=_start_server,
        args=(port,),
        daemon=True,
        name="opcua-test-server",
    )
    thread.start()
    if not _wait_for_server(port, timeout=10.0):
        logger.warning("OPC-UA test server did not become reachable within 10s")
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
    """Thread target: run the OPC-UA server."""
    asyncio.run(_async_server(port))
