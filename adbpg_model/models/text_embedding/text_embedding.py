"""
AnalyticDB Text Embedding Provider

This module implements the text embedding model provider for AnalyticDB PostgreSQL.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from dify_plugin.entities.model import EmbeddingInputType, PriceType
from dify_plugin.entities.model.text_embedding import (EmbeddingUsage,
                                                       TextEmbeddingResult)
from dify_plugin.errors.model import CredentialsValidateFailedError
from dify_plugin.interfaces.model.text_embedding_model import \
    TextEmbeddingModel

# Add models directory to path
models_path = Path(__file__).parent.parent
sys.path.insert(0, str(models_path))

from api_helper import AnalyticDBModelAPIHelper, logger


class AdbpgTextEmbeddingModel(TextEmbeddingModel):
    """
    Text embedding model implementation for AnalyticDB PostgreSQL
    """

    def _invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: Optional[str] = None,
        input_type: EmbeddingInputType = EmbeddingInputType.DOCUMENT,
    ) -> TextEmbeddingResult:
        """
        Invoke text embedding model

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :param user: unique user id
        :param input_type: input type
        :return: embeddings result
        """
        api_helper = AnalyticDBModelAPIHelper(credentials)

        max_chunks = self._get_max_chunks(model, credentials)

        batched_embeddings = []
        total_tokens = 0

        # Process in batches
        for i in range(0, len(texts), max_chunks):
            batch_texts = texts[i : i + max_chunks]
            embeddings_batch, batch_tokens = self.embed_documents(
                api_helper=api_helper, model=model, texts=batch_texts
            )
            total_tokens += batch_tokens
            batched_embeddings.extend(embeddings_batch)

        # Calculate usage with actual token count from API
        usage = self._calc_response_usage(
            model=model, credentials=credentials, tokens=total_tokens
        )

        return TextEmbeddingResult(
            embeddings=batched_embeddings, usage=usage, model=model
        )

    def get_num_tokens(
        self, model: str, credentials: dict, texts: list[str]
    ) -> list[int]:
        """
        Get number of tokens for given prompt messages

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :return: list of token counts
        """
        if len(texts) == 0:
            return []

        tokens = []
        for text in texts:
            tokens.append(self._get_num_tokens_by_gpt2(text))
        return tokens

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            api_helper = AnalyticDBModelAPIHelper(credentials)
            self.embed_documents(api_helper=api_helper, model=model, texts=["ping"])
        except Exception as ex:
            logger.exception(f"Credentials validation failed: {ex}")
            raise CredentialsValidateFailedError(str(ex))

    @staticmethod
    def embed_documents(
        api_helper: AnalyticDBModelAPIHelper, model: str, texts: list[str]
    ) -> tuple[list[list[float]], int]:
        """
        Call out to AnalyticDB's embedding endpoint

        Args:
            api_helper: The API helper instance
            model: The model to use for embedding
            texts: The list of texts to embed

        Returns:
            List of embeddings, one for each text, and tokens usage
        """
        embeddings = []
        embedding_used_tokens = 0

        response = api_helper.text_embedding(input=texts, embedding_model=model)

        if "Results" in response and "Results" in response["Results"]:
            results = response["Results"]["Results"]
            sorted_results = sorted(results, key=lambda x: x.get("Index", 0))
            for result in sorted_results:
                if "Embedding" in result and "Embedding" in result["Embedding"]:
                    embeddings.append(
                        list(map(float, result["Embedding"]["Embedding"]))
                    )

        if "TextTokens" in response:
            embedding_used_tokens = response["TextTokens"]

        return embeddings, embedding_used_tokens

    def _calc_response_usage(
        self, model: str, credentials: dict, tokens: int
    ) -> EmbeddingUsage:
        """
        Calculate response usage

        :param model: model name
        :param credentials: credentials
        :param tokens: input tokens
        :return: usage
        """
        input_price_info = self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.INPUT,
            tokens=tokens,
        )

        usage = EmbeddingUsage(
            tokens=tokens,
            total_tokens=tokens,
            unit_price=input_price_info.unit_price,
            price_unit=input_price_info.unit,
            total_price=input_price_info.total_amount,
            currency=input_price_info.currency,
            latency=time.perf_counter() - self.started_at,
        )
        return usage

    @property
    def _invoke_error_mapping(self) -> dict[type[Exception], list[type[Exception]]]:
        """
        Map model invoke error to unified error
        """
        from dify_plugin.errors.model import (InvokeAuthorizationError,
                                              InvokeBadRequestError,
                                              InvokeConnectionError,
                                              InvokeRateLimitError,
                                              InvokeServerUnavailableError)

        return {
            InvokeConnectionError: [],
            InvokeServerUnavailableError: [],
            InvokeRateLimitError: [],
            InvokeAuthorizationError: [],
            InvokeBadRequestError: [],
        }
