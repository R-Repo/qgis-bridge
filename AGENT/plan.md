# qgis-bridge — Full Implementation Plan

_Last updated: 2026-04-09_

---

## 1. What This Package Does

`qgis-bridge` lets a user push spatial data from a Python environment (Jupyter, VS Code, plain script) directly into a running QGIS Desktop session. One function call results in a new named, styled layer appearing in QGIS.

```python
from qgis_bridge import to_qgis

to_qgis(gdf, layer_name="Risk Zones", color_by="risk_score")
to_qgis("gs://my-bucket/elevation.tif", layer_name="Elevation")
```

```python
import qgis_bridge          # registers .qgis accessor on GeoDataFrame
gdf.qgis.send(layer_name="Risk Zones", color_by="risk_score")
```

---

## 2. Architecture

Two components live in this repository:

```
qgis-bridge/
├── src/qgis_bridge/      ← Python package  (installed by the user in their notebook/script env)
└── qgis_plugin/          ← QGIS plugin     (installed by the user in QGIS)
```

They communicate over a **local TCP socket**. The Python package is the client; the QGIS plugin is the server.

### How a single `to_qgis(gdf, ...)` call works end-to-end

```
Python env                          QGIS Desktop
──────────────────────────────      ──────────────────────────────
to_qgis(gdf, layer_name=...)
  │
  ├─ write gdf → /tmp/qbridge/      (GeoPackage via gdf.to_file())
  │   <uuid>/layer.gpkg
  │
  ├─ generate QML style →           (XML, built from color_by / color_ramp args)
  │   /tmp/qbridge/<uuid>/style.qml
  │
  └─ send JSON over TCP ──────────► plugin receives JSON:
                                     {
                                       "layer_name": "Risk Zones",
                                       "file_path": "/tmp/qbridge/.../layer.gpkg",
                                       "qml_path":  "/tmp/qbridge/.../style.qml",
                                       "layer_type": "vector",
                                       "update_existing": true
                                     }
                                     │
                                     ├─ iface.addVectorLayer(file_path, ...)
                                     ├─ layer.loadNamedStyle(qml_path)
                                     └─ iface.mapCanvas().refresh()

                                     sends back: {"status": "ok", "layer_id": "..."}
```

For a cloud raster URI (e.g. `gs://bucket/file.tif`):
- No temp file is written
- URI is translated to GDAL virtual path (`/vsigs/bucket/file.tif`)
- JSON notification contains the GDAL path directly
- QGIS opens it via `iface.addRasterLayer(gdal_path, layer_name)`

---

## 3. Repository Structure

```
qgis-bridge/
├── src/
│   └── qgis_bridge/
│       ├── __init__.py        ← public API: exports to_qgis, registers accessor on import
│       ├── _core.py           ← to_qgis() — main entry point, dispatches vector vs raster
│       ├── _accessor.py       ← GeoDataFrame .qgis accessor (registered via pandas extension API)
│       ├── _uri.py            ← cloud URI → GDAL virtual filesystem path translation
│       ├── _style.py          ← QML XML generation (graduated, categorized, single symbol)
│       ├── _client.py         ← TCP socket client (connects, sends JSON, reads response)
│       └── _temp.py           ← temp file lifecycle management
│
├── qgis_plugin/
│   ├── __init__.py            ← QGIS plugin entry point (classFactory)
│   ├── metadata.txt           ← required QGIS plugin metadata
│   ├── plugin.py              ← plugin class: initGui, unload, starts/stops server
│   └── server.py              ← Qt TCP server (QTcpServer), message handler, PyQGIS layer loader
│
├── tests/
│   ├── test_uri.py            ← URI translation (no QGIS needed)
│   └── test_style.py          ← QML generation (no QGIS needed)
│
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
└── AGENT/
    ├── plan.md                ← this file
    └── logs/
        ├── 2026-04-09-session-01.md   ← product concept session
        └── 2026-04-09-session-02.md   ← architecture decision session
```

---

## 4. Transport: Local TCP Socket

- **Host**: `localhost` (127.0.0.1) only — never exposed externally
- **Port**: `45678` (default, user-configurable)
- **Protocol**: newline-delimited JSON (`\n` terminated messages)
- **Direction**: client (Python) → server (QGIS plugin), then server sends back one-line JSON response
- **Connection model**: connect → send one message → receive one response → disconnect (stateless per call)

### Why TCP socket over other options

| Option | Rejected because |
|---|---|
| Pure file drop (Reloader plugin) | Requires user to install separate plugin; no acknowledgement; polling latency |
| Full data over socket | Unnecessarily complex; file I/O for local temp is fast enough |
| PostgreSQL NOTIFY | Requires running database |
| HTTP inside QGIS | `http.server` on Qt event loop is awkward; TCP is simpler |
| Named pipe | Platform inconsistency (Unix vs Windows) |

---

## 5. Python Package — Module Responsibilities

### `__init__.py`
- Imports and re-exports `to_qgis`
- Imports `_accessor` so that importing `qgis_bridge` automatically registers `.qgis` on GeoDataFrame (side effect by design — standard pandas accessor pattern)

### `_core.py` — `to_qgis(data, layer_name, ...)`
Dispatch logic:
- `isinstance(data, str)` → raster path → `_handle_raster()`
- Otherwise → vector → `_handle_vector()`

`_handle_vector(gdf, layer_name, color_by, color_ramp, opacity, symbol_type, update_existing)`:
1. Write GeoDataFrame to temp GeoPackage via `gdf.to_file(path, driver="GPKG")`
2. Generate QML via `_style.make_vector_qml(gdf, color_by, color_ramp, opacity, symbol_type)`
3. Write QML to temp file
4. Send notification via `_client.send(message)`
5. Return confirmation string to caller

`_handle_raster(uri, layer_name, band, stretch_min, stretch_max, color_ramp, update_existing)`:
1. Translate URI via `_uri.to_gdal_path(uri)`
2. Send notification (no temp file)
3. Return confirmation string

### `_accessor.py`
```python
@geopandas.api.extensions.register_geodataframe_accessor("qgis")
class QGISAccessor:
    def __init__(self, gdf): self._gdf = gdf
    def send(self, **kwargs): return to_qgis(self._gdf, **kwargs)
```

### `_uri.py`
Pure string manipulation. No dependencies.
```
gs://bucket/path  →  /vsigs/bucket/path
s3://bucket/path  →  /vsis3/bucket/path
az://container/path  →  /vsiaz/container/path
```
Raises `ValueError` with a clear message for unrecognised schemes.

### `_style.py`
Generates minimal valid QML XML for:
- **Single symbol** (default, no `color_by`)
- **Graduated** (numeric column: equal interval, quantile, or jenks with configurable color ramp)
- **Categorized** (string/categorical column)

QML is QGIS's native style format. Generating it from Python means QGIS applies it exactly as if the user created it in the Layer Styling panel — no reimplementation of QGIS's renderer API.

### `_client.py`
Stdlib `socket` only. Connects to `localhost:45678`, sends JSON line, reads response line, closes. Raises a clear `ConnectionRefusedError` subclass with a human-readable message if QGIS is not listening (e.g. `QGISNotRunningError: Could not connect to QGIS. Is the qgis-bridge plugin installed and QGIS open?`).

### `_temp.py`
- Creates per-call subdirectory in OS temp: `/tmp/qbridge/<uuid>/`
- Files are left on disk (QGIS needs them to load the layer); cleanup happens on a best-effort basis using `atexit` or a configurable TTL
- On Windows uses `%TEMP%\qbridge\`

---

## 6. QGIS Plugin — Module Responsibilities

### `metadata.txt`
Required by QGIS plugin manager. Fields: `name`, `qgisMinimumVersion`, `description`, `version`, `author`, `email`, `repository`.

### `__init__.py`
Standard QGIS plugin entry point:
```python
def classFactory(iface):
    from .plugin import QGISBridgePlugin
    return QGISBridgePlugin(iface)
```

### `plugin.py` — `QGISBridgePlugin`
- `initGui()`: starts the TCP server, adds a toolbar button/menu item to show server status
- `unload()`: stops the TCP server, removes UI elements
- Stores reference to `iface`

### `server.py` — `BridgeServer`
Uses Qt's `QTcpServer` so it runs on QGIS's existing Qt event loop — no background thread needed.

On receiving a complete JSON message:
1. Parse JSON
2. Dispatch to `_load_vector(msg)` or `_load_raster(msg)` based on `layer_type`
3. Send back `{"status": "ok", "layer_id": "..."}` or `{"status": "error", "message": "..."}`

`_load_vector(msg)`:
- Check if layer with same name exists (for update_existing logic)
- `layer = QgsVectorLayer(msg["file_path"], msg["layer_name"], "ogr")`
- If `qml_path` present: `layer.loadNamedStyle(msg["qml_path"])`
- `QgsProject.instance().addMapLayer(layer)`
- `iface.mapCanvas().refresh()`

`_load_raster(msg)`:
- `layer = QgsRasterLayer(msg["gdal_path"], msg["layer_name"])`
- `QgsProject.instance().addMapLayer(layer)`
- `iface.mapCanvas().refresh()`

---

## 7. Message Protocol

### Python → QGIS (vector)
```json
{
  "type": "vector",
  "layer_name": "Risk Zones",
  "file_path": "/tmp/qbridge/a1b2c3/layer.gpkg",
  "qml_path": "/tmp/qbridge/a1b2c3/style.qml",
  "update_existing": true
}
```

### Python → QGIS (raster)
```json
{
  "type": "raster",
  "layer_name": "Elevation",
  "gdal_path": "/vsigs/my-bucket/elevation.tif"
}
```

### QGIS → Python (response)
```json
{"status": "ok", "layer_id": "abc123_def456"}
```
```json
{"status": "error", "message": "File not found: /tmp/qbridge/..."}
```

---

## 8. Styling Parameters

### Vector
| Parameter | Type | Default | Notes |
|---|---|---|---|
| `color_by` | str \| None | None | Column name to drive color |
| `color_ramp` | str | `"RdYlGn"` | Any QGIS-named ramp or matplotlib name |
| `opacity` | float | 1.0 | 0.0–1.0 |
| `symbol_type` | str | auto-detected | `"marker"`, `"line"`, `"fill"` |
| `n_classes` | int | 5 | For graduated renderer |

### Raster
| Parameter | Type | Default | Notes |
|---|---|---|---|
| `band` | int | 1 | Band index |
| `stretch_min` | float \| None | None | Auto if None |
| `stretch_max` | float \| None | None | Auto if None |
| `color_ramp` | str | `"Greys"` | |

---

## 9. Error Handling

| Situation | Error raised | Message |
|---|---|---|
| QGIS not open / plugin not running | `QGISNotRunningError` | "Could not connect to QGIS on port 45678. Is the qgis-bridge plugin installed and QGIS open?" |
| `color_by` column not found | `ValueError` | "Column 'risk_score' not found. Available columns: [...]" |
| GeoDataFrame has no CRS | `ValueError` | "GeoDataFrame has no CRS set. Set one with gdf.set_crs(...) before sending." |
| Unrecognised URI scheme | `ValueError` | "Unrecognised URI scheme 'ftp://'. Supported: gs://, s3://, az://" |
| QGIS plugin reports error | `QGISError` | Forwarded message from plugin |

---

## 10. What Is NOT in Scope (v0.1)

- Authentication or credential management of any kind
- QGIS Server (headless) — desktop only
- Windows named pipe transport (TCP works on Windows too)
- Automatic QGIS plugin installation — user installs manually or via QGIS Plugin Manager
- Bi-directional sync (QGIS edits reflected back to Python)
- Multi-QGIS-instance support
- Attribute table interaction

---

## 11. Build and Packaging

- **Python package**: `pip install qgis-bridge` installs `qgis_bridge` from `src/`
- **QGIS plugin**: distributed as a zip of `qgis_plugin/` — installable via QGIS > Plugins > Install from Zip. Will be submitted to the QGIS Plugin Repository once stable.
- **Zero required Python dependencies**: the Python package uses stdlib only (`socket`, `json`, `pathlib`, `tempfile`, `uuid`, `xml.etree.ElementTree`)
- **Soft dependency**: `geopandas` — only needed to use `to_qgis(gdf, ...)` or the `.qgis` accessor; the package does not import it itself

---

## 12. Implementation Status

All modules are implemented. Remaining work is publishing and hardening.

| Module | Status |
|---|---|
| `_uri.py` + `tests/test_uri.py` | Complete |
| `_style.py` + `tests/test_style.py` | Complete |
| `_temp.py` | Complete |
| `_client.py` | Complete |
| `_core.py` | Complete |
| `__init__.py` + `_accessor.py` | Complete |
| `qgis_plugin/server.py` | Complete |
| `qgis_plugin/plugin.py` + `metadata.txt` | Complete |
| CI (GitHub Actions) | Complete |
| PyPI publish workflow | Complete (needs trusted publisher setup) |
| QGIS Plugin Repository | Not yet submitted |
