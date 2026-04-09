# ADR-006: Zero Required Dependencies for the Python Package

**Status:** Accepted
**Date:** 2026-04-09

## Context

The Python package runs in the user's analysis environment alongside libraries such as GeoPandas, NumPy, pandas, and scikit-learn. Geospatial environments are notoriously sensitive to dependency conflicts — adding cloud SDKs (boto3, google-cloud-storage, azure-storage-blob) or other heavy dependencies risks breaking existing installs or adding significant install time and footprint.

The package's responsibilities on the Python side are:
- Translate cloud URIs to GDAL paths (pure string manipulation)
- Write GeoDataFrame to a temp file (via the GeoDataFrame's own `.to_file()` method)
- Generate QML XML (standard XML via stdlib `xml.etree.ElementTree`)
- Send a JSON message over a local socket (stdlib `socket` + `json`)
- Manage temp files (stdlib `pathlib`, `tempfile`, `uuid`, `atexit`)

All of these are achievable with the Python standard library.

## Decision

The `qgis_bridge` Python package has zero required dependencies. All functionality is implemented using the Python standard library only.

**Soft dependencies (not declared in `pyproject.toml`):**
- `geopandas` — used by the caller to produce the GeoDataFrame; `to_file()` is called on the object the user passes in. The package itself never imports GeoPandas. If GeoPandas is not present, `to_qgis(gdf, ...)` will fail at the point where `.to_file()` is called, with a natural AttributeError — not a package import error.
- The accessor registration in `_accessor.py` is guarded so that if GeoPandas is not installed, the import of `qgis_bridge` succeeds silently without the accessor.

## Consequences

- `pip install qgis-bridge` is fast and conflict-free regardless of the user's environment.
- No cloud SDK credentials or configuration are required in the Python package — URI translation is pure string manipulation and QGIS/GDAL handle authentication (see ADR-007).
- The package cannot independently verify that a cloud file exists before passing its path to QGIS. This is acceptable — QGIS will surface a meaningful error if the path is unreachable.
