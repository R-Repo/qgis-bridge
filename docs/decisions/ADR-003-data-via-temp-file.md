# ADR-003: Transfer Vector Data via Temp File, Not Over the Socket

**Status:** Accepted
**Date:** 2026-04-09

## Context

The Python package needs to transfer a GeoDataFrame to the QGIS plugin. Two approaches were considered:

1. **Serialize the GeoDataFrame to GeoJSON and send it over the socket.**
   - Requires framing logic for multi-line, variable-length payloads.
   - The QGIS plugin must deserialize GeoJSON and reconstruct features using PyQGIS APIs.
   - All format handling must be re-implemented on the plugin side.

2. **Write the GeoDataFrame to a temp file and send only the file path over the socket.**
   - File write is handled by GeoPandas `.to_file()` — no custom serialization.
   - The QGIS plugin loads the file using its native OGR provider, which supports GeoJSON, GeoPackage, FlatGeobuf, and many other formats.
   - The socket message remains a small JSON object (paths and metadata only).

## Decision

Write the GeoDataFrame to a temporary directory on the local filesystem and send only the file path in the socket notification. The QGIS plugin loads the file via its OGR data provider.

Temp files are written to `<OS temp dir>/qbridge/<uuid>/layer.geojson`. The UUID per call ensures no collision between concurrent calls. Files are left on disk for QGIS to read after the notification is received; cleanup happens on a best-effort basis via `atexit`.

## Consequences

- File I/O to the local temp directory is fast (well under 100ms for datasets a user would visually inspect on a map) and is not a meaningful bottleneck.
- The plugin stays trivial — it delegates all format handling to QGIS's OGR provider rather than reimplementing it.
- The socket protocol remains minimal: a small JSON object carrying paths and metadata.
- This approach only works when the Python process and QGIS run on the same machine, which is the target use case. Remote or containerised setups are out of scope for v0.1.
- Temp file cleanup is best-effort. In long-running sessions, files accumulate until the Python process exits or the user manually clears them. This is acceptable for a local analysis tool.
