"""
TCP socket client.

Connects to the qgis-bridge QGIS plugin on localhost:PORT,
sends one newline-delimited JSON message, reads one JSON response, closes.

No dependencies beyond stdlib.
"""

import json
import socket

DEFAULT_PORT = 45678


class QGISNotRunningError(ConnectionRefusedError):
    """Raised when the QGIS plugin server is not reachable."""


class QGISError(RuntimeError):
    """Raised when the QGIS plugin reports an error in its response."""


def send(message: dict, port: int = DEFAULT_PORT, timeout: float = 10.0) -> dict:
    """Send a JSON message to the QGIS plugin and return the parsed response."""
    payload = json.dumps(message) + "\n"
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
            sock.sendall(payload.encode("utf-8"))
            # Read until newline (one-message protocol)
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
                if b"\n" in chunk:
                    break
    except ConnectionRefusedError:
        raise QGISNotRunningError(
            f"Could not connect to QGIS on port {port}. "
            "Is the qgis-bridge plugin installed and QGIS open?"
        )

    raw = b"".join(chunks).decode("utf-8").strip()
    if not raw:
        raise QGISError("Empty response from QGIS plugin.")

    response = json.loads(raw)
    if response.get("status") == "error":
        raise QGISError(response.get("message", "Unknown error from QGIS plugin."))
    return response
