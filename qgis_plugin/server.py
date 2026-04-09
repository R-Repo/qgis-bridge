"""
Qt TCP server — runs on QGIS's existing event loop (no background thread needed).

Listens on localhost:45678 for newline-delimited JSON messages from the Python package.
Loads the specified layer into the current QGIS project and returns a JSON response.

Message format (vector):
    {"type": "vector", "layer_name": "...", "file_path": "...", "qml_path": "...", "update_existing": true}

Message format (raster):
    {"type": "raster", "layer_name": "...", "gdal_path": "..."}

Response:
    {"status": "ok", "layer_id": "..."}
    {"status": "error", "message": "..."}
"""

DEFAULT_PORT = 45678
