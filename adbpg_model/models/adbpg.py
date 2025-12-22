"""
AnalyticDB Model Provider

This module implements the main model provider for AnalyticDB PostgreSQL.
"""

import sys
from pathlib import Path
from typing import Any

from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType
from dify_plugin.errors.model import CredentialsValidateFailedError

# Add models directory to path
models_path = Path(__file__).parent
sys.path.insert(0, str(models_path))

from api_helper import AnalyticDBModelAPIHelper, logger


class AdbpgProvider(ModelProvider):
    """
    AnalyticDB for PostgreSQL Model Provider

    Supports LLM, Text Embedding, and Rerank models through AnalyticDB's AI capabilities.
    """

    def validate_provider_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Validate provider credentials by attempting to use an LLM model.

        Args:
            credentials: Provider credentials including access keys and instance info

        Raises:
            CredentialsValidateFailedError: If credentials are invalid
        """
        try:
            # Get LLM model instance to validate credentials
            model_instance = self.get_model_instance(ModelType.LLM)

            # Use a simple model for validation - try qwen-turbo first
            model_instance.validate_credentials(
                model="qwen-turbo", credentials=credentials
            )
        except CredentialsValidateFailedError as ex:
            raise ex
        except Exception as ex:
            logger.exception(
                f"{self.get_provider_schema().provider} credentials validate failed"
            )
            raise CredentialsValidateFailedError(str(ex))
