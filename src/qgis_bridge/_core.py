"""
Core entry point: to_qgis().

Dispatches to vector or raster handling based on the type of `data`.
"""

from __future__ import annotations

from pathlib import Path

from . import _client, _style, _temp
from ._uri import is_cloud_uri, to_gdal_path

_GEOM_TYPE_MAP = {
    "Point": "marker", "MultiPoint": "marker",
    "LineString": "line", "MultiLineString": "line",
    "Polygon": "fill", "MultiPolygon": "fill",
}


def to_qgis(
    data,
    layer_name: str = "layer",
    color_by: str | None = None,
    color_ramp: str = "RdYlGn",
    opacity: float = 1.0,
    symbol_type: str | None = None,
    n_classes: int = 5,
    update_existing: bool = True,
    port: int = _client.DEFAULT_PORT,
) -> dict:
    """Push spatial data into a running QGIS session.

    Args:
        data: A GeoDataFrame (vector) or a cloud URI / local path string (raster).
        layer_name: Name for the layer in QGIS.
        color_by: Column name to drive color. None for single-symbol.
        color_ramp: Color ramp name (e.g. "RdYlGn", "Blues", "Viridis").
        opacity: Layer opacity, 0.0–1.0.
        symbol_type: Override geometry symbol type ("point", "line", "fill").
        n_classes: Number of classes for graduated renderer.
        update_existing: Replace layer with same name if it exists.
        port: TCP port the QGIS plugin listens on.

    Returns:
        Response dict from the QGIS plugin.
    """
    if isinstance(data, (str, Path)):
        return _handle_raster(str(data), layer_name, update_existing, port)
    return _handle_vector(
        data, layer_name, color_by, color_ramp, opacity,
        symbol_type, n_classes, update_existing, port,
    )


def _detect_symbol_type(gdf) -> str:
    """Infer QGIS symbol type from GeoDataFrame geometry."""
    geom_type = gdf.geometry.iloc[0].geom_type if len(gdf) > 0 else "Polygon"
    return _GEOM_TYPE_MAP.get(geom_type, "fill")


def _handle_vector(
    gdf, layer_name, color_by, color_ramp, opacity,
    symbol_type, n_classes, update_existing, port,
) -> dict:
    if gdf.crs is None:
        raise ValueError(
            "GeoDataFrame has no CRS set. Set one with gdf.set_crs(...) before sending."
        )

    sym = symbol_type or _detect_symbol_type(gdf)

    # Generate QML
    if color_by is None:
        qml = _style.make_single_symbol_qml(opacity, sym)
    elif color_by not in gdf.columns:
        raise ValueError(
            f"Column {color_by!r} not found. Available columns: {list(gdf.columns)}"
        )
    elif gdf[color_by].dtype.kind in ("f", "i", "u"):
        qml = _style.make_graduated_qml(
            gdf[color_by].dropna().tolist(), color_by, n_classes, color_ramp, opacity, sym,
        )
    else:
        qml = _style.make_categorized_qml(
            gdf[color_by].dropna().astype(str).tolist(), color_by, color_ramp, opacity, sym,
        )

    # Write temp files
    call_dir = _temp.create_call_dir()
    gpkg_path = call_dir / "layer.gpkg"
    qml_path = call_dir / "style.qml"

    gdf.to_file(gpkg_path, driver="GPKG")
    qml_path.write_text(qml, encoding="utf-8")

    return _client.send({
        "type": "vector",
        "layer_name": layer_name,
        "file_path": str(gpkg_path),
        "qml_path": str(qml_path),
        "update_existing": update_existing,
    }, port=port)


def _handle_raster(uri: str, layer_name: str, update_existing: bool, port: int) -> dict:
    if is_cloud_uri(uri):
        gdal_path = to_gdal_path(uri)
    else:
        gdal_path = uri

    return _client.send({
        "type": "raster",
        "layer_name": layer_name,
        "gdal_path": gdal_path,
        "update_existing": update_existing,
    }, port=port)
