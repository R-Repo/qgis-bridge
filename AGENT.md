# AGENT.md — qgis-bridge

Instructions for AI agents working on this repository.

---

## What This Project Is

`qgis-bridge` lets a user push spatial data from a Python environment (Jupyter, VS Code, scripts) into a running QGIS Desktop session with a single function call. No file exports, no manual imports, no QGIS knowledge required from the user.

```python
from qgis_bridge import to_qgis
to_qgis(gdf, layer_name="Risk Zones", color_by="risk_score")
```

---

## Repository Structure

```
qgis-bridge/
├── src/qgis_bridge/        Python package — installed in the user's analysis env
│   ├── __init__.py         Public API: exports to_qgis, registers .qgis accessor
│   ├── _core.py            to_qgis() — dispatches vector vs raster
│   ├── _accessor.py        GeoDataFrame .qgis accessor (pandas extension API)
│   ├── _uri.py             Cloud URI → GDAL path translation (pure stdlib)
│   ├── _style.py           QML XML generation for vector styling
│   ├── _client.py          TCP socket client (stdlib socket only)
│   └── _temp.py            Temp file lifecycle management
│
├── qgis_plugin/            QGIS plugin — installed inside QGIS
│   ├── __init__.py         classFactory entry point (required by QGIS)
│   ├── metadata.txt        QGIS plugin metadata (required by QGIS)
│   ├── plugin.py           Plugin class: starts/stops the TCP server
│   └── server.py           QTcpServer: receives messages, loads layers via PyQGIS
│
├── tests/                  Tests runnable without QGIS
│   ├── test_uri.py         URI translation tests (complete)
│   └── test_style.py       QML generation tests (placeholder)
│
├── docs/decisions/         Architectural Decision Records (ADRs)
├── AGENT/
│   ├── plan.md             Full implementation plan — read this before making changes
│   └── logs/               Session transcripts (append, never edit past entries)
│
├── pyproject.toml          Python package build config (hatchling, zero deps)
└── AGENT.md                This file
```

---

## Two-Component System

This is the most important thing to understand. There are two separate Python environments:

| Component | Environment | Has access to |
|---|---|---|
| `src/qgis_bridge/` | User's analysis env (pip) | GeoPandas, stdlib |
| `qgis_plugin/` | QGIS internal Python | PyQGIS (`iface`, `QgsProject`), Qt |

They communicate over a **local TCP socket on port 45678**. The Python package is the client; the QGIS plugin is the server.

**The Python package must never import PyQGIS.** It does not require QGIS to be installed.
**The QGIS plugin must never import GeoPandas or any analysis library.**

---

## Key Constraints

- **Never add required dependencies to `pyproject.toml`.** The Python package is stdlib-only by design (ADR-006). If a dependency seems necessary, write an ADR first.
- **Never change the JSON protocol without updating both sides.** The message format in `_client.py` and `server.py` must stay in sync (ADR-009).
- **Never monkey-patch GeoDataFrame.** The accessor uses `@register_geodataframe_accessor` (ADR-005).
- **Never import cloud SDKs** (boto3, google-cloud-storage, etc.) in the Python package (ADR-006, ADR-007).
- **Never expose the socket beyond localhost.** The server binds to 127.0.0.1 only.
- **Read `AGENT/plan.md` before implementing anything.** It specifies module responsibilities and implementation order.

---

## Protocol Reference

### Python → QGIS (vector)
```json
{
  "type": "vector",
  "layer_name": "Risk Zones",
  "file_path": "/tmp/qbridge/a1b2c3/layer.geojson",
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
{"status": "ok", "layer_id": "abc123"}
{"status": "error", "message": "..."}
```

Messages are newline-delimited (`\n` terminated). One message per connection.

---

## Development

### Install the Python package (editable)
```bash
uv sync --group dev      # creates .venv, installs package + dev deps
```

### Run tests (no QGIS required)
```bash
uv run pytest tests/
```

`tests/` only contains tests for pure-stdlib modules (`_uri.py`, `_style.py`). These run in any Python environment with no QGIS.

### What cannot be tested without QGIS
- `_client.py` (requires the plugin's TCP server to be running)
- `qgis_plugin/` (requires QGIS's Python environment and `iface`)

End-to-end testing requires QGIS Desktop open with the plugin installed and active.

### Installing the QGIS plugin for development
Copy or symlink `qgis_plugin/` into the QGIS plugins directory:
- macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/qgis_bridge/`
- Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/qgis_bridge/`
- Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\qgis_bridge\`

Then enable it in QGIS > Plugins > Manage and Install Plugins.

---

## Architectural Decisions

All significant design choices are documented in `docs/decisions/`. **Read the relevant ADR before changing anything it covers.**

| ADR | Topic |
|---|---|
| ADR-001 | Two-component architecture |
| ADR-002 | TCP socket transport |
| ADR-003 | Data via temp file |
| ADR-004 | Styling via QML |
| ADR-005 | Accessor pattern |
| ADR-006 | Zero required dependencies |
| ADR-007 | Cloud URI / no auth surface |
| ADR-008 | Function-first API |
| ADR-009 | Single repository |
| ADR-010 | uv as dev workflow tool |

---

## Coding Standards

- **Small, sensible commits.** Each commit should be one logical change.
- **Best practices always.** Follow Python conventions, type hints where useful, clear naming.
- **Minimal code.** As simple and as few lines as possible without compromising readability. No speculative abstractions, no dead code, no unnecessary comments.

---

## Agent Workflow

### Before making changes
1. Read `AGENT/plan.md` — it defines module responsibilities and implementation order.
2. Read the relevant ADR(s) in `docs/decisions/`.
3. Run `pytest tests/` to confirm baseline.

### When making a significant architectural decision
1. Create a new ADR in `docs/decisions/ADR-NNN-short-title.md`.
2. Add it to the table in this file.
3. Note it in the session log.

### Session logs
- Append a new file to `AGENT/logs/` named `YYYY-MM-DD-session-NN.md` for each working session.
- Record the topic, key decisions made, and a summary of changes.
- Never edit past log entries.
- Only log sessions on this project topic. Unrelated conversations are not logged.
