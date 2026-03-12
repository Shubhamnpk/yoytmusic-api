import os
from importlib import metadata


DEFAULT_APP_VERSION = "0.1.0"


def get_version_payload():
    app_version = os.environ.get("APP_VERSION", DEFAULT_APP_VERSION)
    build_time = os.environ.get("BUILD_TIME")
    try:
        ytmusicapi_version = metadata.version("ytmusicapi")
    except metadata.PackageNotFoundError:
        ytmusicapi_version = None

    return {
        "app_version": app_version,
        "ytmusicapi_version": ytmusicapi_version,
        "build_time": build_time,
    }
