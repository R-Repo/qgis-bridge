"""
GeoDataFrame .qgis accessor.

Registered via the official pandas extension accessor API.
Importing qgis_bridge automatically registers this accessor as a side effect —
the standard pattern for pandas/GeoPandas extension packages.

Usage:
    import qgis_bridge
    gdf.qgis.send(layer_name="Risk Zones", color_by="risk_score")
"""

import pandas as pd

from ._core import to_qgis


@pd.api.extensions.register_dataframe_accessor("qgis")
class QGISAccessor:
    def __init__(self, gdf):
        self._gdf = gdf

    def send(self, **kwargs) -> dict:
        """Push this GeoDataFrame to QGIS. Accepts the same kwargs as to_qgis()."""
        return to_qgis(self._gdf, **kwargs)
