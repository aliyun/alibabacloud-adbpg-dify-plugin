import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params


class UpsertChunks(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"UpsertChunks tool_parameters: {params}")
        response = self.client.upsert_chunks(**params)
        logger.info(f"UpsertChunks response: {response}")
        for key, value in response.items():
            yield self.create_variable_message(key, value)
        yield self.create_json_message(response)
