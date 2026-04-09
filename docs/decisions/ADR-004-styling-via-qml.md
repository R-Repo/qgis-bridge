# ADR-004: Apply Styling via Generated QML Files

**Status:** Accepted
**Date:** 2026-04-09

## Context

The Python package needs to convey styling intent (color by column, color ramp, opacity, symbol type) to QGIS. Two approaches were considered:

1. **Send styling parameters in the JSON message and implement the renderer in the plugin.**
   - The plugin reconstructs a `QgsGraduatedSymbolRenderer` or `QgsCategorizedSymbolRenderer` using PyQGIS renderer APIs.
   - Requires maintaining a custom PyQGIS styling layer on the plugin side.
   - Any styling parameter not explicitly handled is unavailable.

2. **Generate a QML file on the Python side and pass its path in the notification.**
   - QML is QGIS's native XML style format, used internally by all of QGIS's own layer styling tools.
   - Loading a QML in PyQGIS is a single call: `layer.loadNamedStyle(qml_path)`.
   - The plugin needs no renderer knowledge — it just calls one method.

## Decision

Generate a QML file on the Python side from the user's styling arguments (`color_by`, `color_ramp`, `opacity`, `symbol_type`, etc.) and pass its path alongside the data file path in the socket notification. The plugin applies it with `layer.loadNamedStyle()`.

QML generation covers three common cases:
- **Single symbol** — no `color_by`, uniform fill/stroke
- **Graduated** — numeric column with a color ramp and configurable classification method
- **Categorized** — string/categorical column with distinct colors per category

## Consequences

- The plugin is reduced to a thin loader: load file, apply QML, refresh canvas. No renderer logic lives there.
- QML applied via `loadNamedStyle()` is pixel-perfect identical to styling applied through QGIS's own Layer Styling panel — no fidelity loss.
- Generating QML XML from Python requires care but only needs to be implemented once per renderer type. The output is stable XML that does not change with QGIS versions in ways that break basic graduated/categorized renderers.
- Users who want styling beyond what the package generates can pass a pre-existing QML file path directly, bypassing generation entirely.
- Raster styling via QML is also possible but deferred — raster color ramps, band selection, and stretch parameters will be handled separately when raster styling is implemented.
