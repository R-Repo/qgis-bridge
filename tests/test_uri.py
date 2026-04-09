from qgis_bridge._uri import to_gdal_path, is_cloud_uri
import pytest


def test_gs_scheme():
    assert to_gdal_path("gs://my-bucket/path/file.tif") == "/vsigs/my-bucket/path/file.tif"


def test_s3_scheme():
    assert to_gdal_path("s3://my-bucket/path/file.tif") == "/vsis3/my-bucket/path/file.tif"


def test_az_scheme():
    assert to_gdal_path("az://my-container/path/file.tif") == "/vsiaz/my-container/path/file.tif"


def test_unknown_scheme_raises():
    with pytest.raises(ValueError, match="Unrecognised URI scheme"):
        to_gdal_path("ftp://some-server/file.tif")


def test_is_cloud_uri():
    assert is_cloud_uri("gs://bucket/file.tif") is True
    assert is_cloud_uri("s3://bucket/file.tif") is True
    assert is_cloud_uri("/local/path/file.tif") is False
