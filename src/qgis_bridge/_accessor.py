"""
GeoDataFrame .qgis accessor.

Registered via the official pandas extension accessor API.
Importing qgis_bridge automatically registers this accessor as a side effect —
the standard pattern for pandas/GeoPandas extension packages.

Usage:
    import qgis_bridge
    gdf.qgis.send(layer_name="Risk Zones", color_by="risk_score")
"""
