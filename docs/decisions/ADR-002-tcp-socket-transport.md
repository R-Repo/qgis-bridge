# ADR-002: Local TCP Socket as the IPC Transport

**Status:** Accepted
**Date:** 2026-04-09

## Context

The Python package and the QGIS plugin run in separate operating system processes and must communicate in real time. Several IPC mechanisms were considered.

**Options evaluated:**

| Option | Notes |
|---|---|
| Local TCP socket | Stdlib `socket`; works on all platforms; no external services |
| Pure file drop + Reloader plugin | Requires user to install a second QGIS plugin; no acknowledgement; polling latency |
| Full data over socket | Sends bulk GeoJSON over the socket; more complex framing; no benefit over temp file approach |
| PostgreSQL NOTIFY | Real-time and robust, but requires a running PostgreSQL/PostGIS database |
| HTTP server inside QGIS | Awkward to run Python's `http.server` on Qt's event loop; more overhead than raw TCP for this use case |
| Named pipe (Unix domain socket) | Platform inconsistency between Unix and Windows; TCP works uniformly on both |
| File system polling | High latency; no acknowledgement without additional mechanism |

## Decision

Use a local TCP socket on `localhost:45678` as the transport between the Python package and the QGIS plugin.

- The QGIS plugin runs a `QTcpServer` on QGIS's existing Qt event loop — no background thread required.
- The Python package connects using stdlib `socket`, sends one JSON message, reads one JSON response, and closes the connection.
- Port 45678 is the default; it is configurable for environments where that port is already in use.
- The connection is localhost-only and is never exposed externally.

## Consequences

- No external services (no database, no message broker) required.
- The Python package's socket code uses only stdlib — no additional dependencies.
- The Qt event loop integration means the plugin server is non-blocking and does not freeze the QGIS UI.
- Each call is stateless (connect → send → receive → close), which keeps the client and server simple to reason about.
- If QGIS is not open or the plugin is not running, the connection is refused immediately, giving a clear failure mode.
