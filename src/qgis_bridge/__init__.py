from ._core import to_qgis
from . import _accessor  # registers .qgis accessor on GeoDataFrame as side effect

__all__ = ["to_qgis"]
