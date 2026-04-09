# ADR-008: Function-First Public API

**Status:** Accepted
**Date:** 2026-04-09

## Context

The package needs a public Python API. Two shapes were considered:

1. **Class-based API** — the user instantiates a client object and calls methods on it:
   ```python
   client = QGISBridge()
   client.send(gdf, layer_name="Risk Zones")
   ```

2. **Function-based API** — a single importable function:
   ```python
   from qgis_bridge import to_qgis
   to_qgis(gdf, layer_name="Risk Zones")
   ```

The package communicates with QGIS over a stateless TCP connection (connect → send → receive → close per call — see ADR-002). There is no persistent connection to maintain, no session state, and no configuration that varies per instance. A class would add conceptual overhead without providing any value.

The design goal is that the experience should feel as natural as calling `.plot()` on a DataFrame — a single low-friction action with no setup.

## Decision

The primary public API is a single module-level function: `to_qgis(data, layer_name, ...)`.

```python
from qgis_bridge import to_qgis

to_qgis(gdf, layer_name="Risk Zones", color_by="risk_score")
to_qgis("gs://my-bucket/elevation.tif", layer_name="Elevation")
```

The function accepts either a GeoDataFrame or a cloud URI string as its first argument, dispatching internally to vector or raster handling.

A class-based API may be introduced in a future version if persistent connection management or per-session configuration becomes necessary.

## Consequences

- One import, one call — the entire interaction surface for the majority of use cases.
- The function signature grows with optional keyword arguments as features are added, which is idiomatic Python.
- No client object for the user to manage, store, or pass around.
- The accessor (`gdf.qgis.send(...)`) is a thin wrapper over this function, not an alternative implementation.
