import logging
from typing import Any

from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
from alibabacloud_gpdb20160503.client import Client
from alibabacloud_tea_openapi import models as open_api_models
from pydantic import BaseModel


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


def init_logger():
    logger = logging.getLogger("adbpg.endpoints")
    logger.setLevel(logging.INFO)

    _formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    _file_handler = logging.FileHandler("/tmp/adbpg_endpoints.log")
    _file_handler.setLevel(logging.INFO)
    _file_handler.setFormatter(_formatter)
    logger.addHandler(_file_handler)

    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(logging.INFO)
    _console_handler.setFormatter(_formatter)
    logger.addHandler(_console_handler)
    return logger


logger = init_logger()


class AnalyticDBAPIHelperConfig(BaseModel):
    access_key: str
    access_secret: str
    region_id: str
    endpoint: str | None = None
    protocol: str | None = None
    read_timeout: int = 600000
    connect_timeout: int = 600000
    dbinstance_id: str
    namespace: str
    namespace_password: str

    def get_client_params(self) -> dict:
        return {
            "access_key": self.access_key,
            "access_secret": self.access_secret,
            "region_id": self.region_id,
            "endpoint": self.endpoint,
            "protocol": self.protocol,
            "read_timeout": self.read_timeout,
            "connect_timeout": self.connect_timeout,
        }

    def get_client(self) -> Client:
        return build_client(**self.get_client_params())

    @classmethod
    def from_credentials(
        cls, credentials: dict[str, Any]
    ) -> "AnalyticDBAPIHelperConfig":
        return cls(
            access_key=credentials.get("ANALYTICDB_KEY_ID"),
            access_secret=credentials.get("ANALYTICDB_KEY_SECRET"),
            region_id=credentials.get("ANALYTICDB_REGION_ID"),
            endpoint=credentials.get("ANALYTICDB_ENDPOINT"),
            namespace=credentials.get("ANALYTICDB_NAMESPACE"),
            namespace_password=credentials.get("ANALYTICDB_NAMESPACE_PASSWORD"),
            dbinstance_id=credentials.get("ANALYTICDB_DBINSTANCE_ID"),
        )


class AnalyticDBAPIHelper:
    def __init__(self, credentials: dict[str, Any]) -> None:
        self.config = AnalyticDBAPIHelperConfig.from_credentials(credentials)
        self.client = self.config.get_client()

    def query_content_text(
        self,
        knowledgebase: str,
        query: str,
        top_k: int = None,
        use_full_text_retrieval: bool = None,
        rerank_factor: float = None,
        graph_enhance: bool = None,
        filter: str = None,
        recall_window: str = None,
        metrics: str = None,
        include_vector: bool = None,
        hybrid_search: str = None,
        hybrid_search_k: int = None,
        hybrid_search_alpha: float = None,
        include_metadata_fields: str = None,
        include_file_url: bool = None,
        url_expiration: int = None,
        *args,
        **kwargs,
    ) -> dict:
        # Parse recall_window from comma-separated string to list of integers
        parsed_recall_window = None
        if recall_window and isinstance(recall_window, str):
            parts = [p.strip() for p in recall_window.split(",") if p.strip()]
            if len(parts) != 2:
                raise ValueError(
                    f"recall_window must have exactly 2 comma-separated values, got: {len(parts)}"
                )
            try:
                parsed_recall_window = [int(parts[0]), int(parts[1])]
            except ValueError:
                raise ValueError(
                    f"recall_window values must be integers, got: {recall_window}"
                )

        # Convert empty metrics to None (Auto)
        parsed_metrics = metrics if metrics else None

        # Convert empty hybrid_search to None and build hybrid_search_args
        parsed_hybrid_search = hybrid_search if hybrid_search else None
        parsed_hybrid_search_args = None
        if parsed_hybrid_search == "RRF" and hybrid_search_k is not None:
            parsed_hybrid_search_args = {"RRF": {"k": int(hybrid_search_k)}}
        elif parsed_hybrid_search == "Weight" and hybrid_search_alpha is not None:
            parsed_hybrid_search_args = {
                "Weight": {"alpha": float(hybrid_search_alpha)}
            }

        request = gpdb_20160503_models.QueryContentRequest(
            collection=knowledgebase,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            content=query,
            top_k=top_k,
            use_full_text_retrieval=use_full_text_retrieval,
            rerank_factor=rerank_factor,
            graph_enhance=graph_enhance,
            filter=filter,
            recall_window=parsed_recall_window,
            metrics=parsed_metrics,
            include_vector=include_vector,
            hybrid_search=parsed_hybrid_search,
            hybrid_search_args=parsed_hybrid_search_args,
            include_metadata_fields=include_metadata_fields,
            include_file_url=include_file_url,
            url_expiration=url_expiration,
        )
        response = self.client.query_content(request)
        logger.info(f"Query content text response: {response.body.to_map()}")
        return response.body.to_map()
