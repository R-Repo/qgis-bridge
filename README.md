# qgis-bridge

Push spatial data from Python directly into a live QGIS session — no file exports, no manual imports, no QGIS-specific knowledge required.

## Overview

`qgis-bridge` eliminates the friction of moving data between Python analysis environments and QGIS for visualization. Run your spatial analysis in a Jupyter notebook or Python script, then send results to QGIS with a single function call.

## Usage

**Standalone function:**
```python
from qbridge import to_qgis

to_qgis(gdf, layer_name="Risk Zones", color_by="risk_score")
```

**GeoDataFrame accessor (opt-in):**
```python
import qbridge  # registers the .qgis accessor on GeoDataFrame

gdf.qgis.send(layer_name="Risk Zones", color_by="risk_score")
```

**Cloud raster URIs (streamed directly, no local download):**
```python
to_qgis("gs://my-bucket/elevation.tif", layer_name="Elevation")
to_qgis("s3://my-bucket/imagery.tif", layer_name="Imagery")
to_qgis("az://my-container/dem.tif", layer_name="DEM")
```

## Supported Data Types

- **Vector**: GeoDataFrame or any DataFrame with geometry
- **Raster**: Cloud GeoTIFFs via GCS (`gs://`), S3 (`s3://`), or Azure Blob (`az://`)

## Design

- Zero QGIS installation required in the Python environment
- Communicates with an already-running QGIS instance
- No authentication surface — credential resolution handled by QGIS/GDAL
- Works in Jupyter, JupyterLab, VS Code, and plain Python scripts

## Installation

```bash
pip install qgis-bridge
```

## Status

Early development. API subject to change.

## License

MIT
