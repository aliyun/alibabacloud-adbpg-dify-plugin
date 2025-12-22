import os

from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
from alibabacloud_gpdb20160503.client import Client
from alibabacloud_tea_openapi import models as open_api_models


def build_client(
    access_key,
    access_secret,
    region_id,
    endpoint,
    protocol: str | None = None,
    read_timeout: int = 600000,
    connect_timeout: int = 600000,
):
    return Client(
        open_api_models.Config(
            access_key_id=access_key,
            access_key_secret=access_secret,
            region_id=region_id,
            read_timeout=read_timeout,
            connect_timeout=connect_timeout,
            endpoint=endpoint,
            protocol=protocol,
            user_agent="dify_plugin",
        )
    )
