# ADR-001: Two-Component Architecture — Python Package and QGIS Plugin

**Status:** Accepted
**Date:** 2026-04-09

## Context

The goal is to let a user push data from a Python environment (Jupyter, VS Code, plain script) into a running QGIS Desktop session. QGIS Desktop has no built-in HTTP API, socket listener, or remote scripting endpoint. Any external process that wants to communicate with a live QGIS session must go through a QGIS plugin, because that is the only mechanism that runs inside QGIS's process and has access to `iface` and `QgsProject`.

The Python-side component must be installable in the user's analysis environment, which is entirely separate from the QGIS Python environment. These two Python environments are typically isolated from each other — the user's notebook environment does not have access to PyQGIS, and QGIS's internal Python does not have access to the user's analysis libraries.

## Decision

Split the system into two components:

1. **`qgis_bridge` Python package** — installed by the user in their notebook/script environment. Responsible for accepting data, writing temp files, generating QML, and sending a notification over a local socket.

2. **`qgis_plugin`** — installed by the user into QGIS. Responsible for listening on a local socket, receiving notifications, and calling PyQGIS APIs to load and style layers.

Both components live in the same repository so that the protocol between them stays in sync and changes to either side are visible together.

## Consequences

- Users must install two things: the Python package and the QGIS plugin. This is an unavoidable cost given the two-process constraint.
- The Python package has no dependency on PyQGIS and does not require QGIS to be installed in the Python environment.
- The plugin has no dependency on the user's analysis libraries (GeoPandas, NumPy, etc.).
- The shared protocol (JSON message format, port number) is the integration point. Changes to it must be coordinated across both components — this is why they live in one repo.
