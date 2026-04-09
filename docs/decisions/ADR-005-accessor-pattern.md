# ADR-005: GeoDataFrame Integration via Registered Accessor, Not Monkey-Patching

**Status:** Accepted
**Date:** 2026-04-09

## Context

Many users prefer calling methods directly on their GeoDataFrame rather than passing it to a standalone function. Two mechanisms exist for attaching functionality to a class you don't own:

1. **Monkey-patching** — directly assign a method onto `GeoDataFrame` at import time:
   ```python
   GeoDataFrame.to_qgis = to_qgis
   ```
   - Modifies a third-party class globally and silently.
   - Invisible to type checkers (mypy, pyright) and IDE autocomplete.
   - Silent conflict if GeoPandas ever adds a `to_qgis` method natively.
   - Considered bad practice in the Python ecosystem.

2. **Registered accessor** — use the official pandas extension API:
   ```python
   @geopandas.api.extensions.register_geodataframe_accessor("qgis")
   class QGISAccessor: ...
   ```
   - The official, documented mechanism for extending DataFrames without modifying the class.
   - Registers a namespaced sub-object (`.qgis`) rather than a top-level method.
   - Type-checker and IDE-friendly when stub files are provided.
   - Emits a warning (not silently overrides) if the namespace is already taken.
   - Used by established packages in the ecosystem (e.g. `geopandas-stubs`, `movingpandas`).

## Decision

Use the registered accessor pattern. Importing `qgis_bridge` registers a `.qgis` namespace on `GeoDataFrame` as a deliberate, documented side effect — the standard pattern for pandas/GeoPandas extension packages.

```python
import qgis_bridge          # registers .qgis

gdf.qgis.send(layer_name="Risk Zones", color_by="risk_score")
```

The accessor is a thin wrapper; `.send()` calls `to_qgis(self._gdf, ...)` internally.

## Consequences

- The accessor uses `.qgis.send()` rather than `.to_qgis()` directly, because the accessor is a namespace object, not the function itself. This is a minor ergonomic difference and is consistent with how other accessor-based packages work.
- The accessor is only created on demand when `.qgis` is accessed — no overhead for users who don't use it.
- If GeoPandas is not installed, importing `qgis_bridge` still works — the accessor registration is skipped gracefully, and only `to_qgis()` is available.
