"""
Cloud URI → GDAL virtual filesystem path translation.

Pure string manipulation. No dependencies.

Supported schemes:
    gs://bucket/path   →   /vsigs/bucket/path
    s3://bucket/path   →   /vsis3/bucket/path
    az://container/path →  /vsiaz/container/path
"""

_SCHEME_MAP = {
    "gs://": "/vsigs/",
    "s3://": "/vsis3/",
    "az://": "/vsiaz/",
}


def to_gdal_path(uri: str) -> str:
    """Translate a cloud storage URI to a GDAL virtual filesystem path."""
    for scheme, prefix in _SCHEME_MAP.items():
        if uri.startswith(scheme):
            return prefix + uri[len(scheme):]
    supported = ", ".join(_SCHEME_MAP.keys())
    raise ValueError(
        f"Unrecognised URI scheme in {uri!r}. Supported: {supported}"
    )


def is_cloud_uri(value: str) -> bool:
    """Return True if the string looks like a supported cloud storage URI."""
    return any(value.startswith(scheme) for scheme in _SCHEME_MAP)
