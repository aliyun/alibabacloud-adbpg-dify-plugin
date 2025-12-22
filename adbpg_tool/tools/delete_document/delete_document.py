import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params


class DeleteDocument(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"DeleteDocument tool_parameters: {params}")
        response = self.client.delete_document(**params)
        logger.info(f"DeleteDocument response: {response}")
        for key, value in response.items():
            yield self.create_variable_message(key, value)
        yield self.create_json_message(response)
