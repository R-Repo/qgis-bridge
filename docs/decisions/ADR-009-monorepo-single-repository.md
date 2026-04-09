# ADR-009: Single Repository for Python Package and QGIS Plugin

**Status:** Accepted
**Date:** 2026-04-09

## Context

The project has two distributable components: the Python package (`src/qgis_bridge/`) and the QGIS plugin (`qgis_plugin/`). These could be maintained in separate repositories or together in one.

The two components share a protocol: the JSON message format and the port number. Any change to the message schema must be reflected in both the Python client and the QGIS plugin server simultaneously. If they live in separate repositories, coordinating protocol changes requires cross-repo pull requests and creates a risk of the two components falling out of sync.

The components are also conceptually a single product — a user installs both to make the system work. Splitting them across repositories adds friction for contributors who need to understand the full system.

## Decision

Both components live in a single repository (`qgis-bridge`), under separate top-level directories:

```
qgis-bridge/
├── src/qgis_bridge/   ← Python package
└── qgis_plugin/       ← QGIS plugin
```

They are distributed separately (PyPI and QGIS Plugin Repository respectively) but developed together.

## Consequences

- Protocol changes are a single commit that touches both sides — no cross-repo coordination required.
- Contributors can read, understand, and test the full system from one checkout.
- Issues and pull requests cover the full system rather than being split across repos.
- The repository is slightly larger than a single-component project, but not meaningfully so — the plugin is small.
- Versioning must be managed carefully: the Python package version in `pyproject.toml` and the plugin version in `metadata.txt` should be kept in sync.
