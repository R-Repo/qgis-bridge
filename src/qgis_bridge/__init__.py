def __getattr__(name):
    if name == "to_qgis":
        from ._core import to_qgis
        return to_qgis
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["to_qgis"]
