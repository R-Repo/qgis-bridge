# ADR-007: Cloud Raster Support via URI Translation with No Authentication Surface

**Status:** Accepted
**Date:** 2026-04-09

## Context

Users frequently work with cloud-hosted GeoTIFFs (GCS, S3, Azure Blob). A naive implementation would import a cloud SDK, resolve credentials, download the file to a temp location, and pass the local path to QGIS. This would:
- Add heavy cloud SDK dependencies (boto3, google-cloud-storage, azure-storage-blob)
- Require the Python package to handle credential configuration
- Download potentially large files to local disk

GDAL — which QGIS is built on — already has native virtual filesystem drivers for all three providers:

| User URI | GDAL path | GDAL driver |
|---|---|---|
| `gs://bucket/file.tif` | `/vsigs/bucket/file.tif` | VSIGS |
| `s3://bucket/file.tif` | `/vsis3/bucket/file.tif` | VSIS3 |
| `az://container/file.tif` | `/vsiaz/container/file.tif` | VSIAZ |

QGIS streams these files directly via GDAL with no local download. Credential resolution follows each provider's standard chain (Application Default Credentials for GCS, AWS credential chain for S3, Azure credentials for Azure) — all configured within the QGIS/GDAL environment, not the Python package.

## Decision

The Python package translates cloud URIs to GDAL virtual filesystem paths using pure string manipulation and passes the resulting path to QGIS in the socket notification. The package has no authentication surface and imports no cloud SDKs.

```
gs://my-bucket/elevation.tif  →  /vsigs/my-bucket/elevation.tif
```

QGIS receives the GDAL path, opens it using `QgsRasterLayer`, and GDAL handles streaming and authentication using credentials already configured in the user's QGIS environment.

## Consequences

- The Python package remains dependency-free (see ADR-006).
- Users who have cloud credentials working in QGIS get cloud raster support automatically with no additional setup.
- Users who do not have cloud credentials configured in QGIS will see a QGIS-level error when the layer fails to load. The Python package cannot surface this error proactively — it only knows that the notification was delivered, not that the layer loaded successfully.
- Credential configuration is entirely the user's responsibility in their QGIS environment. This is the correct boundary — the package is a data-passing utility, not a cloud access manager.
