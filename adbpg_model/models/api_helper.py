"""
API Helper for AnalyticDB Model Providers

This module provides a simplified API client for model providers (LLM, rerank, text embedding)
separate from the tools API helper to avoid coupling.
"""

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


# Setup logger for models module with file output
logger = logging.getLogger("adbpg.models")
logger.setLevel(logging.INFO)

_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# File handler - write to /tmp
_file_handler = logging.FileHandler("/tmp/adbpg_models.log")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(_formatter)
logger.addHandler(_file_handler)

# Console handler
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
logger.addHandler(_console_handler)


class AnalyticDBModelAPIConfig(BaseModel):
    """Configuration for AnalyticDB Model API"""

    access_key: str
    access_secret: str
    region_id: str
    endpoint: str | None = None
    protocol: str | None = None
    read_timeout: int = 600000
    connect_timeout: int = 600000
    dbinstance_id: str

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
    ) -> "AnalyticDBModelAPIConfig":
        return cls(
            access_key=credentials.get("ANALYTICDB_KEY_ID"),
            access_secret=credentials.get("ANALYTICDB_KEY_SECRET"),
            region_id=credentials.get("ANALYTICDB_REGION_ID"),
            endpoint=credentials.get("ANALYTICDB_ENDPOINT"),
            protocol=credentials.get("ANALYTICDB_PROTOCOL"),
            dbinstance_id=credentials.get("ANALYTICDB_DBINSTANCE_ID"),
        )


class AnalyticDBModelAPIHelper:
    """API Helper for AnalyticDB Model Providers"""

    def __init__(self, credentials: dict[str, Any]) -> None:
        self.config = AnalyticDBModelAPIConfig.from_credentials(credentials)
        self.client = self.config.get_client()

    def chat_stream(
        self,
        messages: list,
        llm_model: str,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        presence_penalty: float = None,
        seed: int = None,
        stop: list[str] = None,
        **kwargs,
    ):
        """
        Stream chat completion without knowledge base

        :param messages: list of message objects with role and content
        :param llm_model: model name
        :param max_tokens: max tokens to generate
        :param temperature: temperature parameter
        :param top_p: top_p parameter
        :param presence_penalty: presence_penalty parameter (maps to API's presence_penalty)
        :param seed: random seed
        :param stop: stop sequences
        :return: streaming response chunks
        """
        # Convert messages to API format
        api_messages = []
        for msg in messages:
            api_messages.append(
                gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestModelParamsMessages(
                    role=msg["role"], content=msg["content"]
                )
            )

        # Build model params - only pass non-None values
        model_params_dict = {
            "model": llm_model,
            "messages": api_messages,
        }

        if max_tokens is not None:
            model_params_dict["max_tokens"] = max_tokens
        if temperature is not None:
            model_params_dict["temperature"] = temperature
        if top_p is not None:
            model_params_dict["top_p"] = top_p
        if presence_penalty is not None:
            model_params_dict["presence_penalty"] = presence_penalty
        if seed is not None:
            model_params_dict["seed"] = seed
        if stop is not None and len(stop) > 0:
            model_params_dict["stop"] = stop

        model_params = (
            gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequestModelParams(
                **model_params_dict
            )
        )

        request = gpdb_20160503_models.ChatWithKnowledgeBaseStreamRequest(
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            include_knowledge_base_results=False,  # No knowledge base for LLM provider
            knowledge_params=None,
            model_params=model_params,
        )

        from darabonba.runtime import RuntimeOptions

        logger.info(
            f"Chat stream request started for model: {llm_model}, message count: {len(api_messages)}"
        )
        chunks = self.client.chat_with_knowledge_base_stream_with_sse(
            request, RuntimeOptions()
        )
        return chunks

    def text_embedding(
        self,
        input: list[str],
        embedding_model: str = None,
        dimension: int = None,
        **kwargs,
    ) -> dict:
        """
        Get text embeddings

        :param input: list of texts to embed
        :param embedding_model: embedding model name
        :param dimension: embedding dimension
        :return: embedding response
        """
        request = gpdb_20160503_models.TextEmbeddingRequest(
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            input=input,
            model=embedding_model,
            dimension=dimension,
        )
        response = self.client.text_embedding(request)
        logger.info(
            f"Text embedding response: {response.body.request_id} {response.body.message}"
        )
        return response.body.to_map()

    def rerank(
        self,
        query: str,
        documents: list[str],
        rerank_model: str = None,
        topk: int = None,
        return_documents: bool = None,
        max_chunks_per_doc: int = None,
        **kwargs,
    ) -> dict:
        """
        Rerank documents

        :param query: search query
        :param documents: list of documents to rerank
        :param rerank_model: rerank model name
        :param topk: number of top results to return
        :param return_documents: whether to return document text
        :param max_chunks_per_doc: max chunks per document
        :return: rerank response
        """
        request = gpdb_20160503_models.RerankRequest(
            dbinstance_id=self.config.dbinstance_id,
            region_id=self.config.region_id,
            query=query,
            documents=documents,
            model=rerank_model,
            top_k=topk,
            return_documents=return_documents,
            max_chunks_per_doc=max_chunks_per_doc,
        )
        response = self.client.rerank(request)
        logger.info(
            f"Rerank response: {response.body.request_id} {response.body.message}"
        )
        return response.body.to_map()
