# qgis-bridge

Push spatial data from Python directly into a live QGIS session — no file exports, no manual imports, no QGIS-specific knowledge required.

## Overview

`qgis-bridge` eliminates the friction of moving data between Python analysis environments and QGIS for visualization. Run your spatial analysis in a Jupyter notebook or Python script, then send results to QGIS with a single function call.

## Usage

**Standalone function:**
```python
from qgis_bridge import to_qgis

to_qgis(gdf, layer_name="Risk Zones", color_by="risk_score")
```

**GeoDataFrame accessor:**
```python
import qgis_bridge  # registers the .qgis accessor on GeoDataFrame

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

The QGIS plugin must also be installed separately inside QGIS (Plugins > Install from Zip), using the `qgis_plugin/` directory from this repository.

## Contributing

This project uses [uv](https://docs.astral.sh/uv/) for development.

```bash
# Install uv (if not already installed)
brew install uv          # macOS
pip install uv           # any platform

# Clone and set up
git clone https://github.com/R-Repo/qgis-bridge
cd qgis-bridge
uv sync --group dev      # creates .venv and installs all dependencies

# Run tests (no QGIS required)
uv run pytest tests/
```

## Status

Early development. API subject to change.

## License

MIT
