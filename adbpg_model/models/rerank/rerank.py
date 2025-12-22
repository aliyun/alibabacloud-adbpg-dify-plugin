"""
AnalyticDB Rerank Provider

This module implements the rerank model provider for AnalyticDB PostgreSQL.
"""

import math
import sys
from pathlib import Path
from typing import Optional

from dify_plugin.entities.model.rerank import RerankDocument, RerankResult
from dify_plugin.errors.model import (CredentialsValidateFailedError,
                                      InvokeAuthorizationError,
                                      InvokeBadRequestError,
                                      InvokeConnectionError, InvokeError,
                                      InvokeRateLimitError,
                                      InvokeServerUnavailableError)
from dify_plugin.interfaces.model.rerank_model import RerankModel

# Add models directory to path
models_path = Path(__file__).parent.parent
sys.path.insert(0, str(models_path))

from api_helper import AnalyticDBModelAPIHelper, logger


class AdbpgRerankModel(RerankModel):
    """
    Rerank model implementation for AnalyticDB PostgreSQL
    """

    def _invoke(
        self,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: Optional[float] = None,
        top_n: Optional[int] = None,
        user: Optional[str] = None,
    ) -> RerankResult:
        """
        Invoke rerank model

        :param model: model name
        :param credentials: model credentials
        :param query: search query
        :param docs: docs for reranking
        :param score_threshold: score threshold
        :param top_n: top n
        :param user: unique user id
        :return: rerank result
        """
        if len(docs) == 0:
            return RerankResult(model=model, docs=[])

        api_helper = AnalyticDBModelAPIHelper(credentials)

        topk = min(top_n, len(docs)) if top_n is not None else len(docs)
        response = api_helper.rerank(
            query=query,
            documents=docs,
            rerank_model=model,
            topk=topk,
            return_documents=True,
        )

        rerank_documents = []

        if not response.get("Results") or not response["Results"].get("Results"):
            return RerankResult(model=model, docs=rerank_documents)

        results = response["Results"]["Results"]

        for result in results:
            relevance_score = result.get("RelevanceScore", 0.0)
            index = result.get("Index", 0)
            document_text = result.get("Document", "")

            # Use sigmoid to normalize score to (0, 1) range
            normalized_score = 1.0 / (1.0 + math.exp(-relevance_score))

            rerank_document = RerankDocument(
                index=index, score=normalized_score, text=document_text
            )

            if score_threshold is not None:
                if normalized_score >= score_threshold:
                    rerank_documents.append(rerank_document)
            else:
                rerank_documents.append(rerank_document)

        return RerankResult(model=model, docs=rerank_documents)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            self.invoke(
                model=model,
                credentials=credentials,
                query="What is the capital of the United States?",
                docs=[
                    "Carson City is the capital city of the American state of Nevada.",
                    "Washington, D.C. is the capital of the United States.",
                ],
                score_threshold=0.0,
            )
        except Exception as ex:
            logger.exception(f"Credentials validation failed: {ex}")
            raise CredentialsValidateFailedError(str(ex))

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        Map model invoke error to unified error
        """
        return {
            InvokeConnectionError: [],
            InvokeServerUnavailableError: [],
            InvokeRateLimitError: [],
            InvokeAuthorizationError: [],
            InvokeBadRequestError: [],
        }
