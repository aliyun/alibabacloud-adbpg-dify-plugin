from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger
from tools.base.api_helper import AnalyticDBAPIHelper


class ListKnowledgeBases(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        logger.info("ListKnowledgeBases invoked")
        response = self.client.list_document_collections()
        for key, value in response.items():
            yield self.create_variable_message(key, value)
        yield self.create_json_message(response)
