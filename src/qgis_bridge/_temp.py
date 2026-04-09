"""
Temp file lifecycle management.

Creates per-call subdirectories under the OS temp dir:
  /tmp/qbridge/<uuid>/layer.geojson
  /tmp/qbridge/<uuid>/style.qml

Files are left on disk for QGIS to read after the call returns.
Best-effort cleanup runs via atexit.
"""

import atexit
import shutil
import tempfile
import uuid
from pathlib import Path

_BASE_DIR = Path(tempfile.gettempdir()) / "qbridge"
_session_dirs: list[Path] = []


def create_call_dir() -> Path:
    """Create a unique temp directory for one to_qgis() call. Returns the path."""
    call_dir = _BASE_DIR / uuid.uuid4().hex[:12]
    call_dir.mkdir(parents=True, exist_ok=True)
    _session_dirs.append(call_dir)
    return call_dir


def _cleanup() -> None:
    """Best-effort removal of all temp dirs created in this session."""
    for d in _session_dirs:
        shutil.rmtree(d, ignore_errors=True)
    _session_dirs.clear()


atexit.register(_cleanup)
