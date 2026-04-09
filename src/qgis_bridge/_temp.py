"""
Temp file lifecycle management.

Creates per-call subdirectories under the OS temp dir:
  /tmp/qbridge/<uuid>/layer.geojson
  /tmp/qbridge/<uuid>/style.qml

Files are left on disk for QGIS to read after the call returns.
Best-effort cleanup runs via atexit.
"""
